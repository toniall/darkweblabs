#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Range collection scorer — Lab 8.7.

The range is a target whose answer key you own. This scores a crawl's output
against that ground truth: recall (real services found), precision (reported
services that are real), mirror collapse (duplicate addresses recognised as one
service), and clone detection (look-alikes flagged, not believed). It reasons
only over the range's own manifest and a crawl file — it touches nothing live.

Crawl-output format (JSON): {"discovered": [ {address, service_id?, role?,
same_as?, flagged_clone?, pgp?, btc?}, ... ]}. role in {"service","mirror",
"clone"}; an address mapping to nothing in the manifest is off-range noise.
--selftest is pure arithmetic over an embedded fixture.
"""
import argparse
import json
import sys


def bind_live(truth, envtext):
    """Bind the answer key to the range that is actually running.

    manifest.json ships placeholder address keys (addr-market, addr-market-clone
    and so on) because onion addresses are ephemeral: the range mints new ones on
    every bring-up. The relationships are the stable truth, the addresses are not.
    The live range records what it published in /content/onions.env as name=onion,
    and the mapping to the placeholders is exactly addr-<name> -> <name>.

    Without this join a live crawl scores zero recall against a perfectly good
    crawl, because every real onion it found is absent from the truth table.
    Unmapped placeholders are left as they are, so a partial map degrades rather
    than silently dropping addresses.
    """
    live = {}
    for line in envtext.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, addr = line.split("=", 1)
        addr = addr.strip()
        if addr and addr != "pending":
            live[name.strip()] = addr

    bound, mapped = {}, 0
    for key, meta in truth["addresses"].items():
        name = key[5:] if key.startswith("addr-") else key
        onion = live.get(name)
        if onion:
            bound[onion] = meta
            mapped += 1
        else:
            bound[key] = meta
    truth["addresses"] = bound
    return truth, mapped


def score(truth, crawl):
    addrs = truth["addresses"]
    logical = set(truth["logical_services"])
    seen = {e["address"]: e for e in crawl.get("discovered", [])}

    # recall: logical services found via any genuine (non-clone) address
    found = set()
    for a, e in seen.items():
        ta = addrs.get(a)
        if ta and not ta.get("clone"):
            found.add(ta["service"])
    found &= logical
    recall = len(found) / len(logical) if logical else 0.0
    missed = sorted(logical - found)

    # precision: of distinct services the crawl REPORTS as real (role!=mirror and
    # not flagged as a clone), how many map to a real logical service? An unflagged
    # clone or an off-range address reported as real is a false positive.
    reported = real = 0
    off_range = []
    for a, e in seen.items():
        if e.get("role") == "mirror" or e.get("same_as"):
            continue
        if e.get("role") == "clone" or e.get("flagged_clone"):
            continue
        reported += 1
        ta = addrs.get(a)
        if ta and not ta.get("clone") and ta.get("service") in logical:
            real += 1
        else:
            off_range.append(a)
    precision = real / reported if reported else 0.0

    # mirror collapse: mirror addresses recognised as the same service
    mirror_addrs = [a for a, t in addrs.items() if t.get("mirror")]
    collapsed = sum(1 for a in mirror_addrs
                    if (e := seen.get(a)) and (e.get("role") == "mirror" or e.get("same_as")))

    # clone detection: clones flagged vs believed (and did it trust the swap?)
    clone_addrs = [a for a, t in addrs.items() if t.get("clone")]
    caught = 0
    believed = []
    for a in clone_addrs:
        e = seen.get(a)
        if e is None:
            continue
        if e.get("role") == "clone" or e.get("flagged_clone"):
            caught += 1
        else:
            t = addrs[a]
            trusted = (e.get("btc") == t.get("clone_btc")) or (e.get("pgp") == t.get("clone_pgp"))
            believed.append({"address": a, "trusted_swapped_payment": bool(trusted)})

    return {
        "recall": round(recall, 2), "found": sorted(found), "missed": missed,
        "precision": round(precision, 2), "reported": reported, "off_range": off_range,
        "mirrors_total": len(mirror_addrs), "mirrors_collapsed": collapsed,
        "clones_total": len(clone_addrs), "clones_caught": caught, "clones_believed": believed,
    }


def render(r):
    out = []
    out.append("scored crawl against range ground truth")
    out.append(f"  services found     {len(r['found'])} / {len(r['found']) + len(r['missed'])}"
               f"     recall    {r['recall']:.2f}"
               + (f"    (missed: {', '.join(r['missed'])})" if r['missed'] else ""))
    out.append(f"  reported real      {r['reported'] - len(r['off_range'])} / {r['reported']}"
               f"     precision {r['precision']:.2f}"
               + (f"    ({len(r['off_range'])} off-range / invented)" if r['off_range'] else ""))
    out.append(f"  mirrors collapsed  {r['mirrors_collapsed']} / {r['mirrors_total']}")
    if r['clones_believed']:
        trusted = any(c['trusted_swapped_payment'] for c in r['clones_believed'])
        tail = " (swapped payment trusted)" if trusted else ""
        out.append(f"  clones caught      {r['clones_caught']} / {r['clones_total']}"
                   f"     FAIL — clone reported as genuine{tail}")
    else:
        out.append(f"  clones caught      {r['clones_caught']} / {r['clones_total']}")
    return "\n".join(out)


# ---- embedded fixture for --selftest ----------------------------------------

_FIXTURE_TRUTH = {
    "logical_services": ["directory", "market", "forum", "leak", "paste"],
    "addresses": {
        "d":  {"service": "directory"},
        "m":  {"service": "market", "pgp": "9A3F", "btc": "bc1q_k7"},
        "f":  {"service": "forum"},
        "l":  {"service": "leak"},
        "p":  {"service": "paste"},
        "mm": {"service": "market", "mirror": True},
        "mc": {"service": "market", "clone": True, "altered": ["pgp", "btc"],
               "genuine_pgp": "9A3F", "genuine_btc": "bc1q_k7",
               "clone_pgp": "2E77", "clone_btc": "bc1q_z9"},
    },
}

_PERFECT = {"discovered": [
    {"address": "d", "role": "service"}, {"address": "m", "role": "service"},
    {"address": "f", "role": "service"}, {"address": "l", "role": "service"},
    {"address": "p", "role": "service"},
    {"address": "mm", "role": "mirror", "same_as": "m"},
    {"address": "mc", "role": "clone", "flagged_clone": True},
]}

# missed paste; two invented; mirror collapsed; clone BELIEVED with swapped btc
_FOOLED = {"discovered": [
    {"address": "d", "role": "service"}, {"address": "m", "role": "service"},
    {"address": "f", "role": "service"}, {"address": "l", "role": "service"},
    {"address": "mm", "role": "mirror", "same_as": "m"},
    {"address": "mc", "role": "service", "pgp": "2E77", "btc": "bc1q_z9"},
    {"address": "x1", "role": "service"}, {"address": "x2", "role": "service"},
]}


def selftest():
    ok = True

    r = score(_FIXTURE_TRUTH, _PERFECT)
    if not (r["recall"] == 1.0 and r["precision"] == 1.0
            and r["mirrors_collapsed"] == 1 and r["clones_caught"] == 1
            and not r["clones_believed"]):
        ok = False

    r = score(_FIXTURE_TRUTH, _FOOLED)
    # 4/5 services (missed paste); mirror collapsed; clone believed + trusted swap
    if not (r["recall"] == 0.8 and r["missed"] == ["paste"]
            and r["mirrors_collapsed"] == 1
            and r["clones_caught"] == 0
            and len(r["clones_believed"]) == 1
            and r["clones_believed"][0]["trusted_swapped_payment"] is True):
        ok = False
    # precision: reported (non-mirror, non-flagged) = m,d,f,l,mc,x1,x2 = 7; real = m,d,f,l = 4
    if not (r["reported"] == 7 and len(r["off_range"]) == 3 and r["precision"] == round(4/7, 2)):
        ok = False

    print("selftest: recall/precision, mirror collapse, and clone detection score")
    print(f"          correctly (a believed clone with a trusted swap is caught)"
          f"  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--truth", help="ground-truth manifest JSON (default: manifest.json beside this file)")
    ap.add_argument("--map", dest="map", metavar="ONIONS_ENV",
                    help="the live range's onions.env (or - for stdin): binds the "
                         "manifest's addr-* placeholders to the addresses actually "
                         "published, so a live crawl can be scored")
    ap.add_argument("crawl", nargs="?", help="crawl-output JSON to score")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.crawl:
        ap.error("provide a crawl-output JSON, or --selftest")

    import os
    tp = a.truth or os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
    truth = json.load(open(tp))
    crawl = json.load(open(a.crawl))

    if a.map:
        envtext = sys.stdin.read() if a.map == "-" else open(a.map).read()
        truth, mapped = bind_live(truth, envtext)
        print(f"  scored against the live range: {mapped} of "
              f"{len(truth['addresses'])} addresses bound to published onions\n")

    print(render(score(truth, crawl)))

#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Persona parsing and hard-identifier links — Chapter 13 (Labs 13.1-13.2).

A persona is a bundle of claims: the handle it wears, the keys it shows and the keys it
actually signs with, the wallets it transacts through, when it is active, and how it
writes. This parses each profile into that record and finds the HARD links — a shared
signed key or a shared wallet, the high-confidence identifiers that on their own justify
merging two personas. The one distinction that matters most lives here: a key a persona
DISPLAYS is not a key it CONTROLS. Someone can advertise a rival's fingerprint to
impersonate or frame them (Chapter 11's borrowed-key vendor), so a displayed-only match is
not a link — it is flagged as possible framing, and only a signed-key match links. The
naive baseline this chapter argues against ignores that distinction and merges on any
shared identifier at all.
"""
import argparse
import glob
import itertools
import os
import sys


def _list(v):
    return [x.strip() for x in v.split(",") if x.strip()]


def parse_persona(text):
    fields, posts, in_posts = {}, [], False
    for line in text.splitlines():
        if line.startswith("--- posts ---"):
            in_posts = True
            continue
        if in_posts:
            posts.append(line)
        elif ":" in line and not line.startswith("==="):
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return {
        "handle": fields.get("persona"),
        "surface": fields.get("surface"),
        "displayed_keys": _list(fields.get("displayed_keys", "")),
        "signed_keys": _list(fields.get("signed_keys", "")),
        "wallets": _list(fields.get("wallets", "")),
        "active_hours": [int(h) for h in _list(fields.get("active_hours", ""))],
        "tactics": _list(fields.get("tactics", "")),
        "posts": "\n".join(posts).strip(),
    }


def load(corpus_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, "persona-*.txt"))):
        rec = parse_persona(open(p).read())
        out[rec["handle"]] = rec
    return out


def edges(personas, naive=False):
    out = []
    for a, b in itertools.combinations(sorted(personas), 2):
        ra, rb = personas[a], personas[b]
        if naive:
            shared_any = (set(ra["displayed_keys"]) | set(ra["signed_keys"])) & \
                         (set(rb["displayed_keys"]) | set(rb["signed_keys"]))
            if shared_any or (set(ra["wallets"]) & set(rb["wallets"])):
                out.append({"a": a, "b": b, "signal": "shared_identifier", "weight": 1.0})
            continue
        if set(ra["signed_keys"]) & set(rb["signed_keys"]):
            out.append({"a": a, "b": b, "signal": "shared_signed_key", "weight": 1.0})
        if set(ra["wallets"]) & set(rb["wallets"]):
            out.append({"a": a, "b": b, "signal": "shared_wallet", "weight": 1.0})
        # displayed but not signed -> provenance gap, not a link
        disp = set(ra["displayed_keys"]) & set(rb["displayed_keys"])
        if disp and not (set(ra["signed_keys"]) & set(rb["signed_keys"])):
            out.append({"a": a, "b": b, "signal": "displayed_only_key", "weight": 0.0,
                        "note": "possible framing — key displayed, not controlled"})
    return out


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    P = load(os.path.join(here, "corpus"))
    ok = True

    nh = P["NightHawk"]
    if not (nh["surface"] == "market" and nh["signed_keys"] == ["F19B7A0C4E82D5613FA0"]
            and len(nh["active_hours"]) == 10 and nh["posts"].startswith("We stand behind")):
        print(f"  NightHawk parse -> {nh}")
        ok = False

    full = edges(P)

    def sig(a, b):
        return {e["signal"] for e in full if {e["a"], e["b"]} == {a, b}}

    if "shared_signed_key" not in sig("NightHawk", "RedLattice") or "shared_wallet" not in sig("NightHawk", "RedLattice"):
        print(f"  Alpha hard link -> {sig('NightHawk','RedLattice')}")
        ok = False
    # Mimic displays Alpha's key but does not sign it -> framing flag, NOT a link
    if sig("Mimic", "NightHawk") != {"displayed_only_key"}:
        print(f"  Mimic/NightHawk -> {sig('Mimic','NightHawk')}")
        ok = False
    # Bravo shares no hard identifier
    if sig("SaltMine", "IronVault"):
        print(f"  Bravo should share no hard identifier -> {sig('SaltMine','IronVault')}")
        ok = False
    # naive merges Mimic into Alpha on the displayed key
    nsig = {e["signal"] for e in edges(P, naive=True) if {e["a"], e["b"]} == {"Mimic", "NightHawk"}}
    if nsig != {"shared_identifier"}:
        print(f"  naive Mimic/NightHawk -> {nsig}")
        ok = False

    print("selftest: personas parse to records; a signed key or wallet links, a displayed-only")
    print(f"          key is flagged as framing not a link, and naive merges on any identifier  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        P = load(a.corpus)
        if a.summary:
            for h, r in P.items():
                sk = ",".join(r["signed_keys"]) or "-"
                dk = ",".join(r["displayed_keys"]) or "-"
                w = ",".join(r["wallets"]) or "-"
                print(f"    {h:12} {r['surface']:7} signs:{sk:22} shows:{dk:22} wallet:{w[:12]}")
        elif a.links:
            for e in edges(P):
                if e["signal"] == "displayed_only_key":
                    print(f"    (framing) {e['a']:12} {e['b']:12} {e['note']}")
                else:
                    print(f"    {e['signal']:18} {e['a']:12} {e['b']}")
        else:
            import json
            print(json.dumps(P, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

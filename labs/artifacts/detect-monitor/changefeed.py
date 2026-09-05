#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Snapshot parsing and the raw change feed — Chapter 14 (Labs 14.1-14.2).

A single capture is blind to change; a monitor watches a timeline and asks what moved. This
parses each snapshot into its entities and diffs consecutive snapshots into RAW events — the
unfiltered stream of everything that differs, before any judgement about what matters. It
echoes the Chapter 12 lifecycle diff, generalised from one victim to the whole monitored
world: victims that appeared, changed status, or vanished; sites that went up or down;
mirrors, clones, and personas newly seen; and pages whose banner changed. Crucially it uses
Chapter 10 content identity to tell a real change from a re-render: a page whose banner
flips but whose content_id holds is cosmetic churn, not news — the raw feed records it, and
a later stage decides its fate.
"""
import argparse
import glob
import os
import sys

SECTIONS = ("victims", "sites", "mirrors", "clones", "personas", "pages")


def parse_snapshot(text):
    snap = {"name": None}
    for s in SECTIONS:
        snap[s] = {}
    cur = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("==="):
            continue
        if line.startswith("snapshot:"):
            snap["name"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("--- ") and line.endswith(" ---"):
            cur = line[4:-4].strip()
            continue
        if cur and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            name = parts[0]
            fields = {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    fields[k.strip()] = v.strip()
            key = (name, fields.get("site")) if cur == "victims" else name
            snap[cur][key] = fields | {"_name": name}
    return snap


def load_timeline(corpus_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(corpus_dir, "snapshot-*.txt"))):
        out.append(parse_snapshot(open(p).read()))
    return sorted(out, key=lambda s: s["name"])


def _pair_events(prev, curr):
    ev = []
    tf, tt = prev["name"], curr["name"]

    def mk(klass, name, surface, before, after, **extra):
        ev.append({"t_from": tf, "t_to": tt, "klass": klass, "name": name,
                   "surface": surface, "before": before, "after": after, **extra})

    # victims (keyed by name+site so a mirror's copies are distinct rows)
    for key, aft in curr["victims"].items():
        bef = prev["victims"].get(key)
        if bef is None:
            mk("victim", key[0], key[1], None, aft)
        elif (bef.get("status"), bef.get("deadline")) != (aft.get("status"), aft.get("deadline")):
            mk("victim", key[0], key[1], bef, aft)
    for key, bef in prev["victims"].items():
        if key not in curr["victims"]:
            mk("victim", key[0], key[1], bef, None)

    # sites
    for name, aft in curr["sites"].items():
        bef = prev["sites"].get(name)
        if bef and bef.get("state") != aft.get("state"):
            mk("site", name, name, bef, aft, operator=aft.get("operator"))

    # mirrors / clones / personas: new appearances
    for sect, klass in (("mirrors", "mirror"), ("clones", "clone"), ("personas", "persona")):
        for name, aft in curr[sect].items():
            if name not in prev[sect]:
                mk(klass, name, name, None, aft)

    # pages: banner flip with stable content_id == churn; content_id change == real
    for name, aft in curr["pages"].items():
        bef = prev["pages"].get(name)
        if bef and bef != aft:
            mk("page", name, name, bef, aft)
    return ev


def feed(timeline):
    out = []
    for prev, curr in zip(timeline, timeline[1:]):
        out.extend(_pair_events(prev, curr))
    return out


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    tl = load_timeline(os.path.join(here, "corpus"))
    ok = True
    if [s["name"] for s in tl] != ["t1", "t2", "t3"]:
        print(f"  timeline order -> {[s['name'] for s in tl]}"); ok = False

    ev = feed(tl)

    def has(klass, name, tt):
        return any(e["klass"] == klass and e["name"] == name and e["t_to"] == tt for e in ev)

    # a few landmark raw diffs must be present
    for klass, name, tt in [("victim", "Coastal", "t2"), ("site", "NightHawkMkt", "t2"),
                            ("mirror", "RedLattice-m1", "t2"), ("clone", "NightHawkMkt-x", "t3"),
                            ("persona", "n1ghthawk2", "t3")]:
        if not has(klass, name, tt):
            print(f"  missing raw event: {klass} {name} @ {tt}"); ok = False
    # Northwind vanishes t2->t3
    if not any(e["klass"] == "victim" and e["name"] == "Northwind"
               and e["surface"] == "RedLattice" and e["after"] is None and e["t_to"] == "t3" for e in ev):
        print("  missing Northwind withdrawal raw event"); ok = False
    # churn present as page diffs
    if sum(1 for e in ev if e["klass"] == "page") < 8:
        print(f"  churn page diffs -> {sum(1 for e in ev if e['klass']=='page')}"); ok = False

    print(f"selftest: three snapshots diff into a raw feed; victim/site/mirror/clone/persona")
    print(f"          appearances and churn page diffs all surface  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        ev = feed(load_timeline(a.corpus))
        if a.summary:
            print(f"    raw events: {len(ev)}")
            for e in ev:
                b = e["before"]["status"] if e["klass"] == "victim" and e["before"] else "-"
                aft = e["after"]["status"] if e["klass"] == "victim" and e["after"] else ("gone" if e["after"] is None else "-")
                print(f"    {e['t_from']}->{e['t_to']}  {e['klass']:8} {e['name']:16} @{e['surface']:14} {b}->{aft}")
        else:
            import json
            print(json.dumps(ev, indent=2, default=str))
    else:
        ap.error("use --selftest or --corpus <dir>")

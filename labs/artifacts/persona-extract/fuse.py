#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Signal fusion into operator clusters — Chapter 13 (Lab 13.5).

This is the chapter. Every prior lab produced typed links between personas — a shared
signed key, a shared wallet, a stylometric match, a shared rhythm, a handle
transformation, a repeated tactic sequence. Fusion combines them under one rule: hard
identifiers dominate and merge on their own, soft signals only merge when they corroborate
one another, and a key that is displayed but not signed is never allowed to merge. Personas
are clustered into operators with the Chapter 10 union-find, and each cluster carries a
CONFIDENCE and an evidence trail — high when hard identifiers hold it together, medium when
only soft signals do — because an attribution an analyst cannot both defend and falsify is
not intelligence. The naive baseline merges on any shared identifier or a look-alike
handle, and makes both errors this design exists to prevent: it merges an operator that
only borrowed a key, and it splits an operator that only rotated one.
"""
import argparse
import itertools
import os
import sys

import behavior
import identifiers
import stylometry

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dedup"))
from cluster import _UF   # reuse Ch10 union-find

STYLE_T = 0.45      # stylometric similarity above this is a soft link
MERGE_T = 0.8       # accumulated edge weight at or above this merges two personas
HARD = {"shared_signed_key", "shared_wallet"}


def _norm(h):
    return behavior._norm_handle(h)


def _within1(x, y):
    if x == y:
        return True
    if abs(len(x) - len(y)) > 1:
        return False
    # one substitution / insertion / deletion
    if len(x) == len(y):
        return sum(a != b for a, b in zip(x, y)) == 1
    lo, hi = (x, y) if len(x) < len(y) else (y, x)
    for i in range(len(hi)):
        if lo == hi[:i] + hi[i + 1:]:
            return True
    return False


def _all_edges(personas, naive=False):
    if naive:
        out = identifiers.edges(personas, naive=True)
        # naive also merges look-alike handles (no provenance, no corroboration)
        for a, b in itertools.combinations(sorted(personas), 2):
            if _within1(_norm(a), _norm(b)):
                out.append({"a": a, "b": b, "signal": "handle_lookalike", "weight": 1.0})
        return out
    return (identifiers.edges(personas) +
            stylometry.style_links(personas, STYLE_T) +
            behavior.edges(personas))


def fuse(personas, naive=False):
    edges = _all_edges(personas, naive=naive)

    pair = {}
    for e in edges:
        key = tuple(sorted((e["a"], e["b"])))
        d = pair.setdefault(key, {"weight": 0.0, "signals": []})
        d["weight"] += e["weight"]
        d["signals"].append(e["signal"])

    uf = _UF(sorted(personas))
    hard_uf = _UF(sorted(personas))
    framing = []
    for (a, b), d in pair.items():
        if "displayed_only_key" in d["signals"] and d["weight"] < MERGE_T:
            framing.append({"a": a, "b": b, "note": "key displayed, not controlled — possible framing"})
        if d["weight"] >= MERGE_T:
            uf.union(a, b)
            if any(s in HARD for s in d["signals"]):
                hard_uf.union(a, b)

    comps = {}
    for h in sorted(personas):
        comps.setdefault(uf.find(h), []).append(h)

    clusters = []
    for i, (_, members) in enumerate(sorted(comps.items(), key=lambda kv: sorted(kv[1])), 1):
        sigs = sorted({s for (a, b), d in pair.items()
                       if a in members and b in members for s in d["signals"]
                       if s != "displayed_only_key"})
        if len(members) == 1:
            conf = "single"
        elif len({hard_uf.find(m) for m in members}) == 1:
            conf = "high"
        else:
            conf = "medium"
        clusters.append({"operator": f"op-{i}", "personas": sorted(members),
                         "confidence": conf, "signals": sigs})
    return {"clusters": clusters, "framing_flags": framing}


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    P = identifiers.load(os.path.join(here, "corpus"))
    ok = True

    full = fuse(P)
    got = sorted(tuple(c["personas"]) for c in full["clusters"])
    want = sorted([
        ("BlackVault", "NightHawk", "RedLattice", "n1ghthawk"),
        ("IronVault", "SaltMine"),
        ("Mimic",),
        ("Nighthawke",),
    ])
    if got != want:
        print(f"  full clusters -> {got}")
        ok = False

    conf = {tuple(c["personas"]): c["confidence"] for c in full["clusters"]}
    if conf.get(("BlackVault", "NightHawk", "RedLattice", "n1ghthawk")) != "high":
        print("  Alpha cluster should be high confidence (hard identifiers)")
        ok = False
    if conf.get(("IronVault", "SaltMine")) != "medium":
        print("  Bravo cluster should be medium confidence (soft only)")
        ok = False
    if not any(f["a"] == "Mimic" or f["b"] == "Mimic" for f in full["framing_flags"]):
        print("  Mimic's borrowed key should raise a framing flag")
        ok = False

    naive = fuse(P, naive=True)
    n_big = max((c["personas"] for c in naive["clusters"]), key=len)
    if not ("Mimic" in n_big and "Nighthawke" in n_big):
        print(f"  naive should over-merge Mimic and Nighthawke into Alpha -> {n_big}")
        ok = False
    if any(set(c["personas"]) == {"IronVault", "SaltMine"} for c in naive["clusters"]):
        print("  naive should split Bravo, not link it")
        ok = False

    print(f"selftest: full recovers 4 operators (Alpha high, Bravo medium) and flags the borrowed")
    print(f"          key; naive over-merges the frame and the look-alike and splits Bravo  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        res = fuse(identifiers.load(a.corpus), naive=a.naive)
        if a.summary:
            for c in res["clusters"]:
                tag = {"high": "HIGH  ", "medium": "medium", "single": "single"}[c["confidence"]]
                print(f"    [{tag}] {c['operator']}: {', '.join(c['personas'])}")
                if c["confidence"] != "single":
                    print(f"             via {', '.join(c['signals'])}")
            for f in res["framing_flags"]:
                print(f"    (framing) {f['a']} vs {f['b']}: {f['note']}")
        else:
            import json
            print(json.dumps(res, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir> [--naive] [--summary]")

#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Behavioural signals — Chapter 13 (Lab 13.4).

Beyond what a persona writes, there is when it is active, what it calls itself, and how it
operates. Three weak signals live here. An activity-hour histogram hints at a working
timezone — a hint, explicitly not an identity, since anyone can post at any hour. A handle
transformation catches the same name lightly disguised (leet substitution, a dropped
character) by normalising handles and testing equality. And a repeated tactic sequence —
the Chapter 12 negotiation signature — recurs across an operator's leak brands. None of
these establishes a link alone; each raises confidence when it coincides with the others,
which is the whole logic of the fusion in Lab 13.5.
"""
import argparse
import itertools
import math
import os
import sys

import identifiers

RHYTHM_T = 0.6            # activity-histogram cosine above this is a rhythm match
_LEET = str.maketrans({"1": "i", "3": "e", "0": "o", "4": "a", "5": "s", "7": "t"})


def _hist(hours):
    h = [0] * 24
    for x in hours:
        if 0 <= x < 24:
            h[x] += 1
    return h


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def rhythm_sim(ra, rb):
    return round(_cos(_hist(ra["active_hours"]), _hist(rb["active_hours"])), 3)


def _norm_handle(h):
    return "".join(c for c in h.lower().translate(_LEET) if c.isalnum())


def handle_transform(ra, rb):
    return _norm_handle(ra["handle"]) == _norm_handle(rb["handle"])


def edges(personas):
    out = []
    for a, b in itertools.combinations(sorted(personas), 2):
        ra, rb = personas[a], personas[b]
        r = rhythm_sim(ra, rb)
        if r >= RHYTHM_T:
            out.append({"a": a, "b": b, "signal": "rhythm", "weight": 0.3, "sim": r})
        if handle_transform(ra, rb):
            out.append({"a": a, "b": b, "signal": "handle_transform", "weight": 0.3})
        if ra["tactics"] and ra["tactics"] == rb["tactics"]:
            out.append({"a": a, "b": b, "signal": "tactic_sequence", "weight": 0.2})
    return out


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    P = identifiers.load(os.path.join(here, "corpus"))
    ok = True

    # handle transform: leet variant matches, look-alike does not
    if not handle_transform(P["NightHawk"], P["n1ghthawk"]):
        print("  NightHawk/n1ghthawk should be a handle transform")
        ok = False
    if handle_transform(P["NightHawk"], P["Nighthawke"]):
        print("  NightHawk/Nighthawke should NOT be a handle transform (look-alike)")
        ok = False

    e = edges(P)

    def sig(a, b):
        return {x["signal"] for x in e if {x["a"], x["b"]} == {a, b}}

    if "rhythm" not in sig("SaltMine", "IronVault"):
        print(f"  Bravo rhythm -> {sig('SaltMine','IronVault')}")
        ok = False
    if "tactic_sequence" not in sig("RedLattice", "BlackVault"):
        print(f"  Alpha tactic sequence -> {sig('RedLattice','BlackVault')}")
        ok = False
    # cross-operator rhythm must not fire (disjoint bands)
    if "rhythm" in sig("NightHawk", "SaltMine") or "rhythm" in sig("Mimic", "Nighthawke"):
        print("  cross-operator rhythm should not fire")
        ok = False

    print("selftest: leet handle variants match and look-alikes do not; shared rhythm and a")
    print(f"          repeated tactic sequence link only within an operator  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--rhythm", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        P = identifiers.load(a.corpus)
        if a.rhythm:
            for a2, b2 in itertools.combinations(sorted(P), 2):
                print(f"    {rhythm_sim(P[a2], P[b2]):.3f}  {a2:12} {b2}")
        elif a.summary:
            for e in edges(P):
                extra = f" ({e['sim']})" if "sim" in e else ""
                print(f"    {e['signal']:16} {e['a']:12} {e['b']}{extra}")
        else:
            import json
            print(json.dumps(edges(P), indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

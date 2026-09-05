#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The watchlist — Chapter 14 (built from Chapter 13's attribution).

Detection is only as good as what it is told to watch, and this chapter watches exactly the
operators Chapter 13 attributed. This runs the Chapter 13 fusion over the persona corpus and
turns every HIGH-confidence operator cluster into a watch entry: the handles it wears and the
hard identifiers — signed keys and wallets — it is known by. Two later decisions rest on it.
A newly seen persona whose signed key is on the watchlist is not a stranger; it is a watched
operator resurfacing under a new mask (an operator_resurface event). And any event touching a
watched operator's surface is boosted in severity, because a change to a known adversary is
worth more than the same change to an unknown one. It reuses Chapter 13 outright — no
re-attribution here, just consumption of its result.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "persona-extract"))
import fuse          # Ch13 fusion
import identifiers   # Ch13 persona loader


def build(persona_corpus_dir):
    personas = identifiers.load(persona_corpus_dir)
    result = fuse.fuse(personas)
    keys, wallets, handles, operators = set(), set(), set(), []
    for c in result["clusters"]:
        if c["confidence"] != "high":
            continue
        k, w = set(), set()
        for h in c["personas"]:
            r = personas[h]
            k |= set(r["signed_keys"])
            w |= set(r["wallets"])
        keys |= k
        wallets |= w
        handles |= set(c["personas"])
        operators.append({"operator": c["operator"], "members": c["personas"],
                          "keys": sorted(k), "wallets": sorted(w), "confidence": c["confidence"]})
    return {"keys": keys, "wallets": wallets, "handles": handles, "operators": operators}


def watches(wl, *, key=None, wallet=None, handle=None):
    return bool((key and key in wl["keys"]) or (wallet and wallet in wl["wallets"])
                or (handle and handle in wl["handles"]))


def _default_corpus():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "persona-extract", "corpus")


def selftest():
    wl = build(_default_corpus())
    ok = True
    if "F19B7A0C4E82D5613FA0" not in wl["keys"]:
        print(f"  Alpha key should be watched -> {sorted(wl['keys'])}"); ok = False
    if not {"NightHawk", "RedLattice"} <= wl["handles"]:
        print(f"  Alpha members should be watched -> {sorted(wl['handles'])}"); ok = False
    if len(wl["operators"]) != 1:  # only Alpha is HIGH confidence in the Ch13 corpus
        print(f"  expected 1 high-confidence watched operator -> {len(wl['operators'])}"); ok = False
    print(f"selftest: the watchlist is built from Chapter 13's high-confidence operators")
    print(f"          ({len(wl['operators'])} operator, {len(wl['keys'])} watched key)  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona-corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    wl = build(a.persona_corpus or _default_corpus())
    if a.summary:
        for op in wl["operators"]:
            print(f"    [{op['confidence']}] {op['operator']}: {', '.join(op['members'])}")
            print(f"             keys {op['keys']}  wallets {[w[:16]+'…' for w in op['wallets']]}")
    else:
        import json
        print(json.dumps({k: (sorted(v) if isinstance(v, set) else v) for k, v in wl.items()}, indent=2))

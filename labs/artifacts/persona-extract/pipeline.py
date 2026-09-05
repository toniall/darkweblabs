#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Linkage pipeline — Chapter 13 (Labs 13.2-13.7).

Runs the whole linkage over the persona corpus: parse personas, gather hard-identifier,
stylometric, and behavioural links, and fuse them into operator clusters with confidence
and a framing-flag list. The naive path is the linker this chapter argues against — it
merges on any shared identifier or a look-alike handle, with no provenance check and no
corroboration requirement. --selftest runs the persona scorer on its own output, naive
versus full.
"""
import argparse
import glob
import json
import os
import sys

import fuse
import identifiers


def run(corpus_dir, naive=False):
    P = identifiers.load(corpus_dir)
    res = fuse.fuse(P, naive=naive)
    return {
        "personas": [{"handle": h, "surface": r["surface"]} for h, r in P.items()],
        "clusters": res["clusters"],
        "framing_flags": res["framing_flags"],
    }


def _summary(out):
    print(f"    personas: {len(out['personas'])}   operators: {len(out['clusters'])}")
    for c in out["clusters"]:
        tag = {"high": "HIGH  ", "medium": "medium", "single": "single"}[c["confidence"]]
        print(f"    [{tag}] {c['operator']}: {', '.join(c['personas'])}")
    if out["framing_flags"]:
        print(f"    framing flags: {len(out['framing_flags'])} (borrowed-key pairs held apart)")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    corpus = os.path.join(here, "corpus")
    sys.path.insert(0, os.path.join(here, "..", "persona-scorer"))
    import scorer

    truth = json.load(open(os.path.join(here, "..", "persona-scorer", "manifest.json")))
    naive = scorer.score(truth, run(corpus, naive=True))
    full = scorer.score(truth, run(corpus, naive=False))

    ok = True
    if not (full["link_recall"] == 1.0 and full["link_precision"] == 1.0
            and full["false_merges"] == 0 and full["operators_found"] == full["operators_true"]
            and full["confidence_ok"] == full["confidence_total"] and full["framing_ok"] == full["framing_total"]):
        print(f"  full -> {full}")
        ok = False
    if not (naive["false_merges"] > 0 and naive["link_precision"] < full["link_precision"]
            and naive["operators_found"] < naive["operators_true"]):
        print(f"  naive -> {naive}")
        ok = False

    print(f"selftest: full recall {full['link_recall']:.2f}/precision {full['link_precision']:.2f}/"
          f"false-merges {full['false_merges']}; naive precision {naive['link_precision']:.2f}/"
          f"false-merges {naive['false_merges']}  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        out = run(a.corpus, naive=a.naive)
        if a.summary:
            _summary(out)
            sys.exit(0)
        text = json.dumps(out, indent=2)
        if a.out:
            open(a.out, "w").write(text)
            print(f"wrote {a.out} ({'naive' if a.naive else 'full linkage'})")
        else:
            print(text)
    else:
        ap.error("use --selftest or --corpus <dir> [--naive] [--summary] [--out file]")

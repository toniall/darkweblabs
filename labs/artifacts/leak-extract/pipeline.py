#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Extraction pipeline — Chapter 12 (Labs 12.2-12.7).

Ties the two surfaces into one run over an extortion operation's corpus: parse the leak
site's victim entries into records, diff the snapshots for lifecycle tells, detect
reposted victims across sites, parse the negotiation transcripts into arcs, and correlate
public claim against private position to flag bluffs. The naive path is the brittle
analyst this chapter argues against — class-only victim parsing, a single snapshot with
no lifecycle, no cross-site repost check, transcripts read for their dollar figure only,
and so no bluffs. --selftest runs the leak scorer on its own output, naive versus full.
"""
import argparse
import glob
import json
import os
import sys

import correlate
import lifecycle
import negotiation
import reposts
import victims


def run(corpus_dir, naive=False):
    victim_records = []
    for p in sorted(glob.glob(os.path.join(corpus_dir, "a-t2-*.html"))):
        name = os.path.basename(p)
        if "index" in name:
            continue
        rec = victims.parse_victim(open(p).read(), naive=naive)
        rec["_file"] = name
        victim_records.append(rec)

    if naive:
        life, rep, bluffs = {}, {}, {}
        negos = {os.path.basename(p): negotiation.parse(open(p).read(), naive=True)
                 for p in sorted(glob.glob(os.path.join(corpus_dir, "nego-*.txt")))}
    else:
        life = lifecycle.diff(corpus_dir)
        rep = reposts.find(corpus_dir)
        negos = {os.path.basename(p): negotiation.parse(open(p).read())
                 for p in sorted(glob.glob(os.path.join(corpus_dir, "nego-*.txt")))}
        bluffs = correlate.build(corpus_dir)

    return {
        "victims": victim_records,
        "lifecycle": {str(k): v for k, v in life.items()},
        "reposts": {str(k): v for k, v in rep.items()},
        "negotiations": negos,
        "bluffs": {str(k): v for k, v in bluffs.items()},
    }


def _summary(out):
    V = out["victims"]
    req = ("victim_id", "org", "sector", "country", "claimed_gb", "status")
    comp = sum(1 for r in V if all(r.get(k) is not None for k in req))
    life = out["lifecycle"]
    slid = [k for k, v in life.items() if v.get("deadline_slid")]
    withdrawn = [k for k, v in life.items() if v.get("transition") == "withdrawn"]
    rep = {k: v["kind"] for k, v in out["reposts"].items()}
    bluffs = {k: v["bluffs"] for k, v in out["bluffs"].items() if v.get("bluffs")}
    print(f"    victims parsed: {len(V)} ({comp} complete)")
    print(f"    lifecycle: slid deadlines={slid} withdrawn={withdrawn}")
    print(f"    reposts: {rep}")
    print(f"    bluffs: {bluffs}")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    corpus = os.path.join(here, "corpus")
    sys.path.insert(0, os.path.join(here, "..", "leak-scorer"))
    import scorer

    truth = json.load(open(os.path.join(here, "..", "leak-scorer", "manifest.json")))
    naive = scorer.score(truth, run(corpus, naive=True))
    full = scorer.score(truth, run(corpus, naive=False))

    ok = True
    if not (naive["lifecycle_recall"] == 0.0 and naive["repost_recall"] == 0.0
            and naive["tactic_recall"] == 0.0 and naive["bluff_recall"] == 0.0):
        print(f"  naive -> {naive}")
        ok = False
    if not (full["victim_completeness"] == 1.0 and full["lifecycle_recall"] == 1.0
            and full["repost_recall"] == 1.0 and full["tactic_recall"] == 1.0
            and full["bluff_recall"] == 1.0):
        print(f"  full -> {full}")
        ok = False
    if not (full["victim_field_recall"] > naive["victim_field_recall"]):
        ok = False

    print(f"selftest: naive lifecycle {naive['lifecycle_recall']:.2f}/reposts {naive['repost_recall']:.2f}/"
          f"bluffs {naive['bluff_recall']:.2f}; full all 1.00  -> {'PASS' if ok else 'FAIL'}")
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
            print(f"wrote {a.out} ({'naive' if a.naive else 'full pipeline'})")
        else:
            print(text)
    else:
        ap.error("use --selftest or --corpus <dir> [--naive] [--summary] [--out file]")

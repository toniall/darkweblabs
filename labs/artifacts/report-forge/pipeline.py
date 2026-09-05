#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The capstone pipeline — Chapter 15 (Lab 15.7).

Runs the whole book end-to-end: chain the four attribution engines into an evidence graph, turn
it into calibrated claims, and assemble the intelligence report — then grade it. The naive path is
the careless write-up this chapter argues against: it assembles the same findings but flattens them
to sourceless, high-confidence fact. --selftest grades both against the ground-truth claim set with
the report scorer, and shows that the difference is not what the report says (coverage is identical)
but whether a decision-maker can audit it.
"""
import argparse
import json
import os
import sys

import evidence as evidence_mod
import claims as claims_mod
import report as report_mod


def run(naive=False):
    return report_mod.assemble(claims_mod.build(evidence_mod.build()), naive=naive)


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "report-scorer"))
    import scorer
    truth = json.load(open(os.path.join(here, "..", "report-scorer", "manifest.json")))
    full = scorer.score(truth, run(naive=False))
    naive = scorer.score(truth, run(naive=True))
    ok = True
    if not (full["coverage"] == 1.0 and full["provenance"] == 1.0 and full["calibration"] == 1.0 and full["overclaims"] == 0):
        print(f"  full -> {full}"); ok = False
    if not (naive["overclaims"] > 0 and naive["provenance"] < full["provenance"] and naive["calibration"] < full["calibration"]):
        print(f"  naive -> {naive}"); ok = False
    if naive["coverage"] != full["coverage"]:
        print(f"  coverage should be identical (both assemble the same findings) -> full {full['coverage']} naive {naive['coverage']}"); ok = False
    print(f"selftest: full provenance {full['provenance']:.2f}/calibration {full['calibration']:.2f}/overclaims "
          f"{full['overclaims']}; naive provenance {naive['provenance']:.2f}/overclaims {naive['overclaims']} at the "
          f"same coverage  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    rep = run(naive=a.naive)
    text = json.dumps(rep, indent=2, default=str)
    if a.out:
        open(a.out, "w").write(text)
        print(f"wrote {a.out} ({'naive' if a.naive else 'full'} report)")
    else:
        print(text)

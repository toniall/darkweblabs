#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Extraction scoring harness — Chapter 11 (Lab 11.7).

The Chapter 8 scorer graded a crawl's coverage; the Chapter 10 scorer graded a dedup
pass's judgment; this grades an extraction run. Against the market-lab ground truth it
reports field recall (are the recovered field values correct), record completeness (are
records whole, or full of holes from markup drift), flag recall (did the graph catch the
scam, the ring, the gamed reputation, the borrowed key), defenses detected (were the
walls recognised), and two safety counts — poisoned pages extracted and honeypots
skipped — because collecting adversarial content as if it were real is its own failure.
Pure Python; ships its answer key and a sample, and self-tests.
"""
import argparse
import json
import os
import sys


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _field_match(gt_val, out_val):
    n1, n2 = _num(gt_val), _num(out_val)
    if n1 is not None and n2 is not None:
        return n1 == n2
    return str(gt_val) == str(out_val)


def score(truth, output):
    # index the output records by their source file
    out_listings = {r.get("_file"): r for r in output.get("listings", [])}
    out_vendors = {r.get("_file"): r for r in output.get("vendors", [])}

    field_ok = field_total = 0
    complete_ok = complete_total = 0

    for fname, gt in truth["listings"].items():
        rec = out_listings.get(fname, {})
        req = [k for k in gt if k != "listing_id"] + ["listing_id"]
        for k in gt:
            field_total += 1
            if _field_match(gt[k], rec.get(k)):
                field_ok += 1
        complete_total += 1
        if all(rec.get(k) is not None for k in gt):
            complete_ok += 1

    for fname, gt in truth["vendors"].items():
        rec = out_vendors.get(fname, {})
        for k in gt:
            field_total += 1
            if _field_match(gt[k], rec.get(k)):
                field_ok += 1
        complete_total += 1
        if all(rec.get(k) is not None for k in gt):
            complete_ok += 1

    # adversarial flags: one point per category recovered exactly
    gt_flags, out_flags = truth["flags"], output.get("flags", {})
    def norm(v):
        return sorted(sorted(x) if isinstance(x, list) else x for x in v)
    flag_ok = sum(1 for cat in gt_flags if norm(out_flags.get(cat, [])) == norm(gt_flags[cat]))
    flag_total = len(gt_flags)

    # defenses recognised
    gt_def, out_def = truth["defenses"], output.get("defenses", {})
    def_ok = sum(1 for p, kind in gt_def.items() if out_def.get(p, {}).get("kind") == kind)
    def_total = len(gt_def)

    return {
        "field_recall": round(field_ok / field_total, 2) if field_total else 1.0,
        "fields_ok": field_ok, "fields_total": field_total,
        "record_completeness": round(complete_ok / complete_total, 2) if complete_total else 1.0,
        "records_complete": complete_ok, "records_total": complete_total,
        "flag_recall": round(flag_ok / flag_total, 2) if flag_total else 1.0,
        "flags_ok": flag_ok, "flags_total": flag_total,
        "defenses_detected": def_ok, "defenses_total": def_total,
        "poisoned_extracted": len(output.get("poisoned_extracted", [])),
        "honeypots_skipped": len(output.get("honeypots_skipped", [])),
    }


def render(res):
    return "\n".join([
        "scored extraction against market-lab ground truth",
        f"  field recall        {res['fields_ok']} / {res['fields_total']}     {res['field_recall']:.2f}",
        f"  record completeness {res['records_complete']} / {res['records_total']}       {res['record_completeness']:.2f}",
        f"  adversarial flags   {res['flags_ok']} / {res['flags_total']}         recall {res['flag_recall']:.2f}",
        f"  defenses detected   {res['defenses_detected']} / {res['defenses_total']}         (captcha queued, never solved)",
        f"  poisoned extracted  {res['poisoned_extracted']}           ({'clean' if res['poisoned_extracted']==0 else 'FAIL — adversarial content taken as real'})",
        f"  honeypots skipped   {res['honeypots_skipped']}",
    ])


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-extraction.json")))
    res = score(truth, sample)
    ok = (res["field_recall"] == 1.0 and res["record_completeness"] == 1.0
          and res["flag_recall"] == 1.0 and res["defenses_detected"] == res["defenses_total"]
          and res["poisoned_extracted"] == 0)
    print(render(res))
    print(f"selftest: grades the sample extraction  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.file:
        here = os.path.dirname(os.path.abspath(__file__))
        truth = json.load(open(os.path.join(here, "manifest.json")))
        print(render(score(truth, json.load(open(a.file)))))
    else:
        ap.error("pass an extraction-output.json or --selftest")

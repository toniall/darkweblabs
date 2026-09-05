#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Extraction scoring harness — Chapter 12 (Lab 12.7).

Grades an extortion-operation extraction against the leak-lab ground truth across both
surfaces. It reports victim field recall and record completeness (does markup drift
empty the leak-site records), lifecycle recall (were the slid deadlines, publications,
and quiet withdrawals recovered from the snapshot diff), repost recall (were the
cross-site mirror and clone called correctly), tactic recall (did the transcript parse
recover the operator's moves), and bluff recall (did the public/private cross-check catch
the theatre, inflation, false sale, and unverifiable deletion). Pure Python; ships its
answer key and a sample, and self-tests.
"""
import argparse
import json
import os
import re
import sys


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _match(a, b):
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return na == nb
    return str(a) == str(b)


def _ratio(caught, total):
    return round(caught / total, 2) if total else 1.0


def score(truth, output):
    out_v = {r.get("_file"): r for r in output.get("victims", [])}

    # victim field recall + completeness (per page)
    f_ok = f_tot = c_ok = c_tot = 0
    for fname, gt in truth["victims"].items():
        rec = out_v.get(fname, {})
        for k in gt:
            f_tot += 1
            if _match(gt[k], rec.get(k)):
                f_ok += 1
        c_tot += 1
        if all(rec.get(k) is not None for k in gt):
            c_ok += 1

    # lifecycle recall — transition and deadline behaviour per victim
    gt_life, out_life = truth["lifecycle"], output.get("lifecycle", {})
    life_ok = sum(1 for vid, g in gt_life.items()
                  if out_life.get(vid, {}).get("transition") == g["transition"]
                  and bool(out_life.get(vid, {}).get("deadline_slid")) == g["deadline_slid"])

    # repost recall — mirror/clone verdict per reposted victim
    gt_rep, out_rep = truth["reposts"], output.get("reposts", {})
    rep_ok = sum(1 for vid, kind in gt_rep.items() if out_rep.get(vid, {}).get("kind") == kind)

    # tactic recall — operator moves recovered across transcripts
    gt_tac, out_neg = truth["tactics"], output.get("negotiations", {})
    tac_ok = tac_tot = 0
    for vid, tactics in gt_tac.items():
        got = set(out_neg.get(f"nego-{vid}.txt", {}).get("tactics", []))
        tac_tot += len(tactics)
        tac_ok += len(set(tactics) & got)

    # bluff recall — public/private inconsistencies caught
    gt_bluff, out_bluff = truth["bluffs"], output.get("bluffs", {})
    bluff_ok = bluff_tot = 0
    for vid, flags in gt_bluff.items():
        got = set(out_bluff.get(vid, {}).get("bluffs", []))
        bluff_tot += len(flags)
        bluff_ok += len(set(flags) & got)

    return {
        "victim_field_recall": _ratio(f_ok, f_tot), "fields_ok": f_ok, "fields_total": f_tot,
        "victim_completeness": _ratio(c_ok, c_tot), "records_complete": c_ok, "records_total": c_tot,
        "lifecycle_recall": _ratio(life_ok, len(gt_life)), "lifecycle_ok": life_ok, "lifecycle_total": len(gt_life),
        "repost_recall": _ratio(rep_ok, len(gt_rep)), "reposts_ok": rep_ok, "reposts_total": len(gt_rep),
        "tactic_recall": _ratio(tac_ok, tac_tot), "tactics_ok": tac_ok, "tactics_total": tac_tot,
        "bluff_recall": _ratio(bluff_ok, bluff_tot), "bluffs_ok": bluff_ok, "bluffs_total": bluff_tot,
    }


def render(res):
    return "\n".join([
        "scored extraction against leak-lab ground truth",
        f"  victim field recall  {res['fields_ok']} / {res['fields_total']}     {res['victim_field_recall']:.2f}",
        f"  record completeness  {res['records_complete']} / {res['records_total']}       {res['victim_completeness']:.2f}",
        f"  lifecycle recall     {res['lifecycle_ok']} / {res['lifecycle_total']}       {res['lifecycle_recall']:.2f}   (slid deadlines, publications, withdrawals)",
        f"  repost recall        {res['reposts_ok']} / {res['reposts_total']}       {res['repost_recall']:.2f}   (mirror = affiliate, clone = recycled)",
        f"  tactic recall        {res['tactics_ok']} / {res['tactics_total']}     {res['tactic_recall']:.2f}",
        f"  bluff recall         {res['bluffs_ok']} / {res['bluffs_total']}       {res['bluff_recall']:.2f}   (theatre, inflation, false sale, unverifiable delete)",
    ])


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-extraction.json")))
    res = score(truth, sample)
    ok = (res["victim_field_recall"] == 1.0 and res["victim_completeness"] == 1.0
          and res["lifecycle_recall"] == 1.0 and res["repost_recall"] == 1.0
          and res["tactic_recall"] == 1.0 and res["bluff_recall"] == 1.0)
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

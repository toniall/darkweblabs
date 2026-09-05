#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Linkage scoring harness — Chapter 13 (Lab 13.7).

Grades a persona-linkage result against the persona-lab ground truth, over persona pairs.
It reports link recall (were the true within-operator links found), link precision (were
the links it drew correct), and — the metric that matters most here — the false-merge
count, the number of pairs it linked across distinct operators, because over-linking is a
false accusation and the dangerous error in attribution. It also checks the operator count,
whether recovered clusters carry the right confidence (calibration), and whether the
borrowed-key pairs were flagged as framing rather than merged. Pure Python; ships its answer
key and a sample, and self-tests.
"""
import argparse
import itertools
import json
import os
import sys


def _pairs(members):
    return {frozenset(p) for p in itertools.combinations(sorted(members), 2)}


def _ratio(n, d):
    return round(n / d, 2) if d else 1.0


def score(truth, output):
    true_ops = truth["operators"]
    true_pairs = set()
    for op in true_ops:
        true_pairs |= _pairs(op["personas"])

    pred_clusters = output.get("clusters", [])
    pred_pairs = set()
    for c in pred_clusters:
        pred_pairs |= _pairs(c["personas"])

    inter = true_pairs & pred_pairs
    false_merges = len(pred_pairs - true_pairs)

    # confidence calibration on exactly-recovered multi-persona operators
    pred_by_set = {frozenset(c["personas"]): c.get("confidence") for c in pred_clusters}
    multi = [op for op in true_ops if len(op["personas"]) > 1]
    conf_ok = sum(1 for op in multi
                  if pred_by_set.get(frozenset(op["personas"])) == op["confidence"])

    # framing flags
    true_fr = {frozenset(p) for p in truth.get("framing_pairs", [])}
    pred_fr = {frozenset((f["a"], f["b"])) for f in output.get("framing_flags", [])}
    framing_ok = len(true_fr & pred_fr)

    return {
        "link_recall": _ratio(len(inter), len(true_pairs)), "links_ok": len(inter), "links_true": len(true_pairs),
        "link_precision": _ratio(len(inter), len(pred_pairs)), "links_pred": len(pred_pairs),
        "false_merges": false_merges,
        "operators_found": len(pred_clusters), "operators_true": len(true_ops),
        "confidence_ok": conf_ok, "confidence_total": len(multi),
        "framing_ok": framing_ok, "framing_total": len(true_fr),
    }


def render(r):
    return "\n".join([
        "scored persona linkage against persona-lab ground truth",
        f"  link recall            {r['links_ok']} / {r['links_true']}      {r['link_recall']:.2f}",
        f"  link precision         {r['links_ok']} / {r['links_pred']}     {r['link_precision']:.2f}",
        f"  false merges           {r['false_merges']}          (cross-operator links — the dangerous error)",
        f"  operators recovered    {r['operators_found']} / {r['operators_true']}",
        f"  confidence calibration {r['confidence_ok']} / {r['confidence_total']}      (high for hard, medium for soft-only)",
        f"  framing flagged        {r['framing_ok']} / {r['framing_total']}      (borrowed key held apart, not merged)",
    ])


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-linkage.json")))
    r = score(truth, sample)
    ok = (r["link_recall"] == 1.0 and r["link_precision"] == 1.0 and r["false_merges"] == 0
          and r["operators_found"] == r["operators_true"]
          and r["confidence_ok"] == r["confidence_total"] and r["framing_ok"] == r["framing_total"])
    print(render(r))
    print(f"selftest: grades the sample linkage  -> {'PASS' if ok else 'FAIL'}")
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
        ap.error("pass a linkage-output.json or --selftest")

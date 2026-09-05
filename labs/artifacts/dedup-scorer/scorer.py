#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Dedup scoring harness — Chapter 10 (Lab 10.7).

The Chapter 8 scorer grades a crawl's coverage; this grades a dedup pass's judgment.
Given a detector's clustering and the clone-lab ground truth, it reports four
numbers: how many same-operator mirrors were correctly grouped (mirror recall), how
many impersonating clones were caught and flagged (clone recall), how many flagged
clones were really clones (clone precision), and how many unrelated services were
wrongly merged (false merges — the cost of turning the thresholds up too far).
Pure Python; ships its answer key and a sample, and self-tests.
"""
import argparse
import json
import os
import sys


def _index(truth):
    """address -> (cluster_name, role) from the ground-truth manifest."""
    idx = {}
    for cname, c in truth["clusters"].items():
        idx[c["canonical"]] = (cname, "canonical")
        for m in c["mirrors"]:
            idx[m] = (cname, "mirror")
        for m in c["clones"]:
            idx[m] = (cname, "clone")
    return idx


def _output_index(output):
    """address -> (output_cluster_id, role) from the detector's clustering."""
    idx = {}
    for i, cl in enumerate(output.get("clusters", [])):
        for member in cl.get("members", []):
            idx[member["address"]] = (i, member.get("role", "canonical"))
    return idx


def score(truth, output):
    gt = _index(truth)
    out = _output_index(output)

    # canonical address per ground-truth cluster, and its output cluster id
    gt_canonical = {c["canonical"]: name for name, c in truth["clusters"].items()}
    out_cluster_of = {a: out[a][0] for a in out}

    def grouped_with_canonical(addr, cname):
        canon = truth["clusters"][cname]["canonical"]
        return (addr in out_cluster_of and canon in out_cluster_of
                and out_cluster_of[addr] == out_cluster_of[canon])

    # mirror recall
    mirrors = [(a, c) for a, (c, r) in gt.items() if r == "mirror"]
    m_ok = [a for a, c in mirrors
            if grouped_with_canonical(a, c) and out.get(a, (None, ""))[1] == "mirror"]
    mirror_recall = len(m_ok) / len(mirrors) if mirrors else 1.0

    # clone recall
    clones = [(a, c) for a, (c, r) in gt.items() if r == "clone"]
    c_ok = [a for a, c in clones
            if grouped_with_canonical(a, c) and out.get(a, (None, ""))[1] == "clone"]
    clone_recall = len(c_ok) / len(clones) if clones else 1.0

    # clone precision
    flagged = [a for a, (i, r) in out.items() if r == "clone"]
    flagged_real = [a for a in flagged if gt.get(a, ("", ""))[1] == "clone"]
    clone_precision = len(flagged_real) / len(flagged) if flagged else 1.0

    # false merges: address pairs co-clustered in the output but in different GT clusters
    false_merges = 0
    addrs = [a for a in out if a in gt]
    for i in range(len(addrs)):
        for j in range(i + 1, len(addrs)):
            a, b = addrs[i], addrs[j]
            if out_cluster_of[a] == out_cluster_of[b] and gt[a][0] != gt[b][0]:
                false_merges += 1

    return {
        "mirror_recall": round(mirror_recall, 2),
        "mirrors_grouped": len(m_ok), "mirrors_total": len(mirrors),
        "clone_recall": round(clone_recall, 2),
        "clones_caught": len(c_ok), "clones_total": len(clones),
        "clone_precision": round(clone_precision, 2),
        "clones_flagged": len(flagged),
        "false_merges": false_merges,
        "missed_mirrors": sorted(a for a, c in mirrors if a not in m_ok),
        "missed_clones": sorted(a for a, c in clones if a not in c_ok),
    }


def render(res):
    lines = ["scored dedup against clone-lab ground truth"]
    mm = f"   (missed: {', '.join(res['missed_mirrors'])})" if res["missed_mirrors"] else ""
    cm = f"   (missed: {', '.join(res['missed_clones'])})" if res["missed_clones"] else ""
    lines.append(f"  mirrors grouped   {res['mirrors_grouped']} / {res['mirrors_total']}"
                 f"     recall    {res['mirror_recall']:.2f}{mm}")
    lines.append(f"  clones caught     {res['clones_caught']} / {res['clones_total']}"
                 f"     recall    {res['clone_recall']:.2f}{cm}")
    lines.append(f"  clone precision   {res['clones_flagged']} flagged"
                 f"      precision {res['clone_precision']:.2f}")
    fm = "  false merges      0     (no unrelated services merged)" if res["false_merges"] == 0 \
        else f"  false merges      {res['false_merges']}     FAIL — unrelated services merged"
    lines.append(fm)
    return "\n".join(lines)


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    truth = json.load(open(os.path.join(here, "manifest.json")))
    sample = json.load(open(os.path.join(here, "sample-clusters.json")))
    res = score(truth, sample)
    # the shipped sample is a full-engine run: everything grouped, both clones caught, clean
    ok = (res["mirror_recall"] == 1.0 and res["clone_recall"] == 1.0
          and res["clone_precision"] == 1.0 and res["false_merges"] == 0)
    print(render(res))
    print(f"selftest: grades the sample clustering  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="a dedup-output.json to score")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.file:
        here = os.path.dirname(os.path.abspath(__file__))
        truth = json.load(open(os.path.join(here, "manifest.json")))
        print(render(score(truth, json.load(open(a.file)))))
    else:
        ap.error("pass a dedup-output.json or --selftest")

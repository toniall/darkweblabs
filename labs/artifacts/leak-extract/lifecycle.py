#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Victim lifecycle over time — Chapter 12 (Lab 12.3).

One snapshot of a leak site is a list of assertions; two snapshots are evidence. A
victim moves through a lifecycle — teased, counted down, published, sold, or quietly
withdrawn — and the transitions are where the pressure tactics show. A deadline that
slides later between snapshots is countdown theatre: the threat that was supposed to be
imminent simply moves, which means it was leverage, not a schedule. A victim that
disappears without being published was most likely paid or pulled. This diffs the
snapshots per victim and classifies each transition, and the two tells it surfaces —
slid deadlines and quiet withdrawals — feed the bluff cross-check in Lab 12.6.
"""
import argparse
import glob
import os
import re
import sys

import victims


def _date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _snapshot(corpus_dir, snap):
    out = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, f"a-{snap}-*.html"))):
        if "index" in p or "drift" in p:
            continue
        rec = victims.parse_victim(open(p).read())
        if rec["victim_id"] is not None:
            out[rec["victim_id"]] = rec
    return out


def diff(corpus_dir):
    t1 = _snapshot(corpus_dir, "t1")
    t2 = _snapshot(corpus_dir, "t2")
    out = {}
    for vid in sorted(set(t1) | set(t2)):
        a, b = t1.get(vid), t2.get(vid)
        if not (a and b):
            continue
        d1, d2 = _date(a["deadline"]), _date(b["deadline"])
        slid = bool(d1 and d2 and d2 > d1)
        if b["status"] == "published":
            trans = "published"
        elif b["status"] == "withdrawn":
            trans = "withdrawn"
        elif a["status"] != b["status"]:
            trans = "escalated"
        else:
            trans = "stable"
        out[vid] = {
            "org": b["org"], "from_status": a["status"], "to_status": b["status"],
            "deadline_from": a["deadline"], "deadline_to": b["deadline"],
            "transition": trans, "deadline_slid": slid,
        }
    return out


def summary(corpus_dir):
    d = diff(corpus_dir)
    return {
        "slid_deadlines": sorted(v for v in d if d[v]["deadline_slid"]),
        "published": sorted(v for v in d if d[v]["transition"] == "published"),
        "withdrawn": sorted(v for v in d if d[v]["transition"] == "withdrawn"),
        "escalated": sorted(v for v in d if d[v]["transition"] == "escalated"),
    }


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    d = diff(os.path.join(here, "corpus"))
    ok = True

    if not d[1001]["deadline_slid"]:
        print(f"  1001 slid -> {d[1001]}")
        ok = False
    if d[1002]["transition"] != "published":
        print(f"  1002 -> {d[1002]}")
        ok = False
    if d[1003]["transition"] != "withdrawn":
        print(f"  1003 -> {d[1003]}")
        ok = False
    if d[1004]["transition"] != "stable":
        print(f"  1004 -> {d[1004]}")
        ok = False
    if d[1005]["transition"] != "escalated":
        print(f"  1005 -> {d[1005]}")
        ok = False

    print("selftest: diffing snapshots catches the slid deadline (1001), the published victim")
    print(f"          (1002), and the quiet withdrawal (1003)  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        if a.summary:
            s = summary(a.corpus)
            print(f"    slid deadlines (countdown theatre): {s['slid_deadlines']}")
            print(f"    published:  {s['published']}")
            print(f"    withdrawn (quiet — paid or pulled): {s['withdrawn']}")
            print(f"    escalated:  {s['escalated']}")
        else:
            import json
            print(json.dumps(diff(a.corpus), indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

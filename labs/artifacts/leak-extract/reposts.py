#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Reposted victims across leak sites — Chapter 12 (Lab 12.4).

The same victim appearing on two leak sites is Chapter 10's mirror-versus-clone question
in a new costume. If a second site carries the identical claim, it is almost always
affiliate movement — an operator who changed brands but kept the victim — which is a
mirror of the claim. If it carries the same victim with an inflated or altered claim, it
is a recycled clone: someone reusing a name to manufacture fresh pressure. The victim is
matched across sites by its entry, using the Chapter 10 shingler to confirm the two are
near-duplicate reposts, and the mirror/clone verdict then turns on whether the claim
held or grew. The value is attribution: a mirror links two brands to one operator, which
is exactly the thread Chapter 13 pulls.
"""
import argparse
import glob
import os
import sys

import victims

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dedup"))
import shingle   # reuse Ch10 text similarity to confirm a near-duplicate repost

REPOST_SIM = 0.5   # two entries this similar in content are the same victim reposted


def _site(fname):
    return "RedLattice" if fname.startswith("a-") else "BlackVault"


def find(corpus_dir):
    # site A latest snapshot (t2) plus every site B entry
    entries = []
    for p in sorted(glob.glob(os.path.join(corpus_dir, "a-t2-*.html")) +
                    glob.glob(os.path.join(corpus_dir, "b-*.html"))):
        name = os.path.basename(p)
        if "index" in name or "drift" in name:
            continue
        body = open(p).read()
        rec = victims.parse_victim(body)
        if rec["victim_id"] is not None:
            entries.append((_site(name), rec["victim_id"], rec, body))

    by_vid = {}
    for site, vid, rec, body in entries:
        by_vid.setdefault(vid, []).append((site, rec, body))

    reposts = {}
    for vid, group in by_vid.items():
        sites = {g[0] for g in group}
        if len(sites) < 2:
            continue
        (sa, ra, ba) = next(g for g in group if g[0] == "RedLattice")
        (sb, rb, bb) = next(g for g in group if g[0] == "BlackVault")
        sim = shingle.text_similarity(ba, bb)
        if sim < REPOST_SIM:
            continue                      # not actually the same entry reposted
        kind = "mirror" if ra["claimed_gb"] == rb["claimed_gb"] else "clone"
        reposts[vid] = {
            "org": ra["org"], "sites": sorted(sites), "kind": kind,
            "similarity": round(sim, 2),
            "claim_a": ra["claimed_gb"], "claim_b": rb["claimed_gb"],
        }
    return reposts


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    r = find(os.path.join(here, "corpus"))
    ok = True

    if not (1004 in r and r[1004]["kind"] == "mirror" and r[1004]["claim_a"] == r[1004]["claim_b"]):
        print(f"  1004 -> {r.get(1004)}")
        ok = False
    if not (1005 in r and r[1005]["kind"] == "clone" and r[1005]["claim_a"] != r[1005]["claim_b"]):
        print(f"  1005 -> {r.get(1005)}")
        ok = False

    print("selftest: Apex reposted with the same claim is affiliate movement (mirror);")
    print(f"          GraniteWorks reposted inflated is a recycled claim (clone)  -> {'PASS' if ok else 'FAIL'}")
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
        r = find(a.corpus)
        if a.summary:
            for vid, d in sorted(r.items()):
                print(f"    {d['org']:24} {d['kind']:6} across {d['sites']}  "
                      f"claim {d['claim_a']} vs {d['claim_b']} GB")
        else:
            import json
            print(json.dumps(r, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

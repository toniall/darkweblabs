#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""The bluff is in the gap — Chapter 12 (Lab 12.6).

An extortion operation stages claims on two surfaces, and the two do not have to agree.
The leak site manufactures pressure in public; the negotiation reveals the operator's
real position in private; and the distance between them is the bluff. This correlates a
victim's public claim against its private transcript and flags four gaps. A deadline that
slid between snapshots was theatre, not a schedule. A claimed volume far larger than the
volume the operator could prove is inflation. A victim advertised as already sold while
the operator is still negotiating is using the sale as leverage. And a promise to delete
exfiltrated data is unverifiable by construction. This is Chapter 10's lesson taken to
its limit — a published claim is not a fact — turned into a check an analyst can run for
a victim staring down a countdown.
"""
import argparse
import glob
import os
import sys

import lifecycle
import negotiation
import victims

VOLUME_RATIO = 5      # claimed volume more than this multiple of proven volume is inflation


def _latest_victims(corpus_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, "a-t2-*.html"))):
        name = os.path.basename(p)
        if "index" in name or "drift" in name:
            continue
        rec = victims.parse_victim(open(p).read())
        if rec["victim_id"] is not None:
            out[rec["victim_id"]] = rec
    return out


def _transcripts(corpus_dir):
    out = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, "nego-*.txt"))):
        vid = int(os.path.basename(p).split("-")[1].split(".")[0])
        out[vid] = negotiation.parse(open(p).read())
    return out


def build(corpus_dir):
    vics = _latest_victims(corpus_dir)
    life = lifecycle.diff(corpus_dir)
    negos = _transcripts(corpus_dir)

    out = {}
    for vid, nego in negos.items():
        vic = vics.get(vid, {})
        bluffs = []
        # deadline theatre — the public countdown moved later between snapshots
        if life.get(vid, {}).get("deadline_slid"):
            bluffs.append("deadline_bluff")
        # inflated volume — claimed far exceeds what the operator could prove
        if vic.get("claimed_gb") and nego.get("proof_gb") and \
                vic["claimed_gb"] > VOLUME_RATIO * nego["proof_gb"]:
            bluffs.append("volume_bluff")
        # sold as leverage — advertised sold in public, still negotiating in private
        if vic.get("status") == "sold" and nego.get("outcome") == "ongoing":
            bluffs.append("sold_bluff")
        # unverifiable deletion — the promise cannot be confirmed
        if "deletion_promise" in nego.get("tactics", []):
            bluffs.append("deletion_bluff")
        out[vid] = {"org": vic.get("org") or nego.get("victim"), "bluffs": bluffs}
    return out


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    b = build(os.path.join(here, "corpus"))
    ok = True

    expected = {
        1001: ["deadline_bluff", "volume_bluff", "deletion_bluff"],
        1002: [],
        1003: ["deletion_bluff"],
        1004: ["sold_bluff"],
    }
    for vid, exp in expected.items():
        got = b.get(vid, {}).get("bluffs")
        if got != exp:
            print(f"  {vid} bluffs -> {got}  (expected {exp})")
            ok = False

    print("selftest: cross-checking public claim against private transcript flags the slid")
    print(f"          deadline, the inflated volume, the sold-as-leverage, the unverifiable delete"
          f"  -> {'PASS' if ok else 'FAIL'}")
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
        b = build(a.corpus)
        if a.summary:
            for vid, d in sorted(b.items()):
                verdict = ", ".join(d["bluffs"]) if d["bluffs"] else "no bluff (claim held)"
                print(f"    {d['org']:24} -> {verdict}")
        else:
            import json
            print(json.dumps(b, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

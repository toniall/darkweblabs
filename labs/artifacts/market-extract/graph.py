#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Vendor graph, reputation, and adversarial checks — Chapter 11 (Labs 11.5, 11.6).

Records are not the product; the graph over them is. Vendors link to listings link to
categories, and the intelligence is in the patterns: who is prolific, which listings
are the same item posted under two handles (a resale ring, found by reusing the
Chapter 10 clusterer on listing bodies), which fingerprints are shared across handles
(a borrowed key, the same signal Chapter 10 used to flag impersonation), which
reputations were earned faster than time allows, and which prices are bait. Every one
of these is the market lying in its own data, and the lesson is Chapter 10's dated
clone verdict generalised: an extracted record is a claim with a provenance and a
confidence, never a fact. This module reuses the dedup shingler and signals so the two
chapters agree on what "the same" and "the same key" mean.
"""
import argparse
import glob
import os
import re
import statistics
import sys

import listings
import vendors

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dedup"))
import cluster as dedup_cluster   # reuse Ch10 union-find for resale-ring grouping
import shingle                    # reuse Ch10 text similarity (content, not template)

REF = (2026, 7, 30)   # "now" for reputation-velocity checks (the book's date)
SCAM_FRACTION = 0.5   # a price below this fraction of the category median is bait
VELOCITY_MAX = 100    # feedback per month above this is not physically plausible
RING_SIM = 0.6        # listing bodies this similar in CONTENT are the same item reposted


def _months_since(datestr):
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", datestr or "")
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)
    months = (REF[0] - y) * 12 + (REF[1] - mo) + (REF[2] - d) / 30.0
    return max(months, 0.5)


def load(corpus_dir):
    """Parse listings (deduped by id — drift variants collapse) and vendors."""
    L = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, "listing-*.html"))):
        rec = listings.parse_listing(open(p).read())
        rec["_file"] = os.path.basename(p)
        if rec["listing_id"] is not None and rec["listing_id"] not in L:
            L[rec["listing_id"]] = rec
    V = {}
    for p in sorted(glob.glob(os.path.join(corpus_dir, "vendor-*.html"))):
        rec = vendors.parse_vendor(open(p).read())
        if rec["handle"]:
            V[rec["handle"]] = rec
    return L, V


def _resale_rings(corpus_dir, L):
    """Group listings whose bodies are near-identical in CONTENT (not just template),
    reusing the Ch10 union-find; a group spanning >1 vendor is a resale ring."""
    recs = list(L.values())
    bodies = {rec["_file"]: open(os.path.join(corpus_dir, rec["_file"])).read() for rec in recs}
    file_vendor = {rec["_file"]: rec["vendor"] for rec in recs}
    file_id = {rec["_file"]: rec["listing_id"] for rec in recs}
    names = sorted(bodies)
    uf = dedup_cluster._UF(names)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if shingle.text_similarity(bodies[names[i]], bodies[names[j]]) >= RING_SIM:
                uf.union(names[i], names[j])
    rings = []
    for group in uf.groups():
        if len(group) > 1 and len({file_vendor[m] for m in group}) > 1:
            rings.append(sorted(file_id[m] for m in group))
    return sorted(rings)


def build(corpus_dir):
    L, V = load(corpus_dir)

    # prolific vendors by listing count
    counts = {}
    for rec in L.values():
        counts[rec["vendor"]] = counts.get(rec["vendor"], 0) + 1
    prolific = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    # resale rings (reused clusterer)
    rings = _resale_rings(corpus_dir, L)

    # borrowed keys: one fingerprint advertised under more than one handle
    by_key = {}
    for h, rec in V.items():
        if rec["pgp"]:
            by_key.setdefault(rec["pgp"], []).append(h)
    borrowed = sorted([sorted(hs) for hs in by_key.values() if len(hs) > 1])

    # gamed reputation: feedback earned faster than time allows
    gamed = []
    for h, rec in V.items():
        months = _months_since(rec["join_date"])
        if months and rec["feedback_count"] and rec["feedback_count"] / months > VELOCITY_MAX:
            gamed.append(h)
    gamed.sort()

    # scam prices: a listing far below its category's median price
    by_cat = {}
    for rec in L.values():
        if rec["price"] is not None and rec["category"]:
            by_cat.setdefault(rec["category"], []).append(rec["price"])
    medians = {c: statistics.median(ps) for c, ps in by_cat.items()}
    scam = sorted(rec["listing_id"] for rec in L.values()
                  if rec["price"] is not None and rec["category"] in medians
                  and rec["price"] < SCAM_FRACTION * medians[rec["category"]])

    return {
        "vendors": [{"handle": h, "listings": counts.get(h, 0),
                     "rating": V[h]["rating"], "pgp": V[h]["pgp"]} for h in sorted(V)],
        "listings": [{"id": i, "vendor": L[i]["vendor"], "category": L[i]["category"],
                      "price": L[i]["price"]} for i in sorted(L)],
        "prolific": prolific,
        "flags": {"resale_rings": rings, "borrowed_keys": borrowed,
                  "gamed_reputation": gamed, "scam_prices": scam},
    }


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    g = build(os.path.join(here, "corpus"))
    f = g["flags"]
    ok = True

    if f["resale_rings"] != [[1001, 1006]]:
        print(f"  resale_rings -> {f['resale_rings']}")
        ok = False
    if f["borrowed_keys"] != [["Mimic", "NightHawk"]]:
        print(f"  borrowed_keys -> {f['borrowed_keys']}")
        ok = False
    if f["gamed_reputation"] != ["SaltMine"]:
        print(f"  gamed_reputation -> {f['gamed_reputation']}")
        ok = False
    if f["scam_prices"] != [1005]:
        print(f"  scam_prices -> {f['scam_prices']}")
        ok = False
    if g["prolific"][0] != ("NightHawk", 2):
        print(f"  prolific -> {g['prolific']}")
        ok = False

    print("selftest: the graph flags the resale ring, the borrowed key, the gamed reputation,")
    print(f"          and the bait price — the market lying in its own data  -> {'PASS' if ok else 'FAIL'}")
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
        g = build(a.corpus)
        if a.summary:
            f = g["flags"]
            print(f"    vendors: {len(g['vendors'])}   listings: {len(g['listings'])}")
            print(f"    prolific: {g['prolific']}")
            print(f"    resale rings:     {f['resale_rings']}")
            print(f"    borrowed keys:    {f['borrowed_keys']}")
            print(f"    gamed reputation: {f['gamed_reputation']}")
            print(f"    bait prices:      {f['scam_prices']}")
        else:
            import json
            print(json.dumps(g, indent=2))
    else:
        ap.error("use --selftest or --corpus <dir>")

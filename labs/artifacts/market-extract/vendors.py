#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Vendor extraction — Chapter 11 (Lab 11.2, continued).

A vendor profile is the other half of the market's schema: a handle, a PGP fingerprint
that is supposed to be the vendor's stable identity, a rating, a join date, and a
feedback history. Extraction recovers that record with the same class-then-label
resilience the listing parser uses. Two fields matter beyond their face value and are
carried forward for Lab 11.6: the PGP fingerprint (because a fingerprint reused across
handles is impersonation, cross-checked with the Chapter 10 signals) and the join date
against the feedback history (because reputation earned faster than time allows is
bought). This module only reads the fields; judging them is the graph's job.
"""
import argparse
import glob
import os
import re
import sys

from listings import _by_class, _by_label, _text   # reuse the resilient field helpers


def _handle(html):
    h = _by_class(html, "vendor-handle")
    if h:
        return h
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    return _text(m.group(1)) if m else None


def _field(html, cls, label, naive=False):
    v = _by_class(html, cls)
    if v is None and not naive:
        v = _by_label(html, label)
    return v


def _feedback_dates(html):
    return re.findall(r'<span[^>]*class=["\']?fb-date["\']?[^>]*>\s*([\d-]+)\s*</span>', html, re.I)


def parse_vendor(html, naive=False):
    """Extract a typed vendor record (handle, pgp, rating, join date, feedback)."""
    rating = _field(html, "v-rating", "Rating", naive)
    fbcount = _field(html, "v-feedback", "Feedback", naive)
    return {
        "handle": _handle(html),
        "pgp": _field(html, "v-pgp", "PGP", naive),
        "rating": float(rating) if rating and re.match(r"^[\d.]+$", rating) else None,
        "join_date": _field(html, "v-joined", "Joined", naive),
        "feedback_count": int(fbcount) if fbcount and fbcount.isdigit() else None,
        "feedback_dates": _feedback_dates(html),
    }


REQUIRED = ("handle", "pgp", "rating", "join_date", "feedback_count")


def is_complete(record):
    return all(record.get(k) is not None for k in REQUIRED)


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    C = {os.path.basename(p): open(p).read()
         for p in glob.glob(os.path.join(here, "corpus", "vendor-*.html"))}
    ok = True

    n = parse_vendor(C["vendor-nighthawk.html"])
    if not (n["handle"] == "NightHawk" and n["pgp"] == "9A3F1C4D7E20B5F8C6D1"
            and n["rating"] == 4.8 and n["join_date"] == "2021-03"
            and n["feedback_count"] == 342 and is_complete(n)):
        print(f"  nighthawk -> {n}")
        ok = False

    # the gamed vendor: joined a fortnight ago, 500 feedback — the numbers 11.6 will judge
    s = parse_vendor(C["vendor-saltmine.html"])
    if not (s["join_date"] == "2026-07-25" and s["feedback_count"] == 500):
        print(f"  saltmine -> {s}")
        ok = False

    # the borrowed-key vendor advertises NightHawk's fingerprint
    m = parse_vendor(C["vendor-mimic.html"])
    if m["pgp"] != n["pgp"]:
        print(f"  mimic pgp {m['pgp']} should equal nighthawk {n['pgp']}")
        ok = False

    print("selftest: vendor profiles parse to typed records, carrying the fingerprint and")
    print(f"          join-vs-feedback history the graph will judge  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

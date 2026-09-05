#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Leak-site victim extraction — Chapter 12 (Lab 12.2).

A dedicated leak site is a database of victims wearing a threat as a skin, and each
entry is the same record: the organisation, its sector and country, the claimed data
volume, the proof the operator offers, the publication status, and a countdown. This
recovers that record with the same class-then-label resilience Chapter 11 used for
listings, so a restyle of the leak site does not silently empty the fields. Every field
is a claim the operator staged for effect — the volume especially — and later labs test
each against the private negotiation. This module only reads them.
"""
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "market-extract"))
from listings import _by_class, _by_label, _text   # reuse Ch11's resilient field helpers


def _org(html):
    for cls in ("v-org", "org"):
        v = _by_class(html, cls)
        if v:
            return v
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", html, re.I | re.S)
    return _text(m.group(1)) if m else None


def _victim_id(html):
    m = re.search(r'data-id=["\']?(\d+)', html)
    if m:
        return int(m.group(1))
    m = re.search(r'Entry\s*#\s*(\d+)', html, re.I)
    return int(m.group(1)) if m else None


def _volume_gb(raw):
    if not raw:
        return None
    m = re.search(r'([\d.]+)\s*GB', raw, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r'([\d.]+)\s*TB', raw, re.I)
    return float(m.group(1)) * 1000 if m else None


def _field(html, cls, label, naive=False):
    v = _by_class(html, cls)
    if v is None and not naive:
        v = _by_label(html, label)
    return v


def parse_victim(html, naive=False):
    """Extract a typed victim record. naive=True keys only to classes and drops fields
    on markup drift; the default falls back to each field's label."""
    return {
        "victim_id": _victim_id(html),
        "org": _org(html),
        "sector": _field(html, "f-sector", "Sector", naive),
        "country": _field(html, "f-country", "Country", naive),
        "claimed_gb": _volume_gb(_field(html, "f-volume", "Data", naive)),
        "proof": _field(html, "f-proof", "Proof", naive),
        "status": _field(html, "f-status", "Status", naive),
        "deadline": _field(html, "f-deadline", "Deadline", naive),
    }


REQUIRED = ("victim_id", "org", "sector", "country", "claimed_gb", "status")


def is_complete(record):
    return all(record.get(k) is not None for k in REQUIRED)


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    C = {os.path.basename(p): open(p).read()
         for p in glob.glob(os.path.join(here, "corpus", "*.html"))}
    ok = True

    r = parse_victim(C["a-t2-1001.html"])
    if not (r["victim_id"] == 1001 and r["org"] == "Northwind Logistics"
            and r["sector"] == "Manufacturing" and r["claimed_gb"] == 200.0
            and r["status"] == "countdown" and r["deadline"] == "2026-08-12" and is_complete(r)):
        print(f"  1001 -> {r}")
        ok = False

    # a 1TB claim normalises to GB
    apex = parse_victim(C["a-t2-1004.html"])
    if apex["claimed_gb"] != 1000.0:
        print(f"  apex volume -> {apex['claimed_gb']}")
        ok = False

    # the drift variant: naive drops the table-only fields, resilient recovers them
    naive = parse_victim(C["a-t2-1003-drift.html"], naive=True)
    full = parse_victim(C["a-t2-1003-drift.html"], naive=False)
    if is_complete(naive):
        print("  naive should NOT complete the drifted entry")
        ok = False
    if not (is_complete(full) and full["org"] == "Coastal Credit Union"
            and full["status"] == "withdrawn" and full["claimed_gb"] == 80.0):
        print(f"  drift full -> {full}")
        ok = False

    print("selftest: victim entries parse to typed records, and label fallback recovers a")
    print(f"          drifted entry the class-only parser drops  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Listing extraction — Chapter 11 (Lab 11.2).

A market publishes its catalogue as a schema behind a web form: every listing detail
page carries the same fields — vendor, title, category, price, where it ships from and
to, terms. Extraction recovers that record. The catch is markup drift: the same field
appears in a table on one page and a definition list on another, so a parser keyed only
to one layout silently drops fields the moment the market restyles. The resilient parser
reads the obvious structure first and then falls back to the field's label wherever it
sits, which is the difference between a record with holes and a complete one. Price is
normalised to an amount and a currency; everything is emitted as one typed record.
"""
import argparse
import glob
import os
import re
import sys

_TAG = re.compile(r"<[^>]+>")


def _text(s):
    return re.sub(r"\s+", " ", _TAG.sub(" ", s)).strip()


def _by_class(html, cls):
    m = re.search(r'<[^>]*class=["\']?%s["\']?[^>]*>(.*?)</' % re.escape(cls), html, re.I | re.S)
    return _text(m.group(1)) if m else None


def _by_label(html, label):
    """Find a label -> value pair regardless of layout: table cells or a <dl>."""
    # <td>Label</td><td>value</td>
    m = re.search(r'<td[^>]*>\s*%s\s*</td>\s*<td[^>]*>(.*?)</td>' % re.escape(label), html, re.I | re.S)
    if m:
        return _text(m.group(1))
    # <dt>Label</dt><dd>value</dd>
    m = re.search(r'<dt[^>]*>\s*%s\s*</dt>\s*<dd[^>]*>(.*?)</dd>' % re.escape(label), html, re.I | re.S)
    if m:
        return _text(m.group(1))
    return None


def _title(html):
    for cls in ("listing-title", "title"):
        t = _by_class(html, cls)
        if t:
            return t
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", html, re.I | re.S)
    return _text(m.group(1)) if m else None


def _listing_id(html):
    m = re.search(r'data-id=["\']?(\d+)', html)
    if m:
        return int(m.group(1))
    m = re.search(r'Listing\s*#\s*(\d+)', html, re.I)
    return int(m.group(1)) if m else None


def _price(raw):
    if not raw:
        return None, None
    m = re.search(r'([\d.]+)\s*([A-Z]{3})', raw)
    if m:
        return float(m.group(1)), m.group(2)
    m = re.search(r'([\d.]+)', raw)
    return (float(m.group(1)), None) if m else (None, None)


def parse_listing(html, naive=False):
    """Extract a typed listing record. naive=True keys only to the primary layout
    (class selectors) and drops fields on drift; the default adds label fallback."""
    def field(cls, label):
        v = _by_class(html, cls)
        if v is None and not naive:              # resilient fallback: find it by its label
            v = _by_label(html, label)
        return v

    price_raw = field("f-price", "Price")
    amount, currency = _price(price_raw)
    return {
        "listing_id": _listing_id(html),
        "title": _title(html),
        "vendor": field("f-vendor", "Vendor"),
        "category": field("f-category", "Category"),
        "price": amount,
        "currency": currency,
        "ships_from": field("f-from", "Ships from"),
        "ships_to": field("f-to", "Ships to"),
        "terms": field("f-terms", "Terms"),
    }


REQUIRED = ("listing_id", "title", "vendor", "category", "price", "ships_from", "ships_to", "terms")


def is_complete(record):
    return all(record.get(k) is not None for k in REQUIRED)


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    C = {os.path.basename(p): open(p).read()
         for p in glob.glob(os.path.join(here, "corpus", "listing-*.html"))}
    ok = True

    r = parse_listing(C["listing-1001.html"])
    if not (r["listing_id"] == 1001 and r["vendor"] == "NightHawk"
            and r["category"] == "hardware" and r["price"] == 180.0
            and r["currency"] == "USD" and is_complete(r)):
        print(f"  1001 -> {r}")
        ok = False

    # the drift variant: naive drops the table-only fields, resilient recovers them
    naive = parse_listing(C["listing-1003-v2.html"], naive=True)
    full = parse_listing(C["listing-1003-v2.html"], naive=False)
    if is_complete(naive):
        print("  naive should NOT complete the drifted listing")
        ok = False
    if not (is_complete(full) and full["vendor"] == "PaperTrail"
            and full["price"] == 45.0 and full["ships_to"] == "worldwide"):
        print(f"  drift full -> {full}")
        ok = False

    print("selftest: listings parse to typed records, and label fallback recovers a drifted")
    print(f"          page the class-only parser drops  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

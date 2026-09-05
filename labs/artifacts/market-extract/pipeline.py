#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Extraction pipeline — Chapter 11 (Labs 11.4, 11.7).

Ties the pieces into one run over a market corpus: parse every listing and vendor page
into records, classify each page the market serves against the defense detector (so a
CAPTCHA wall is queued not extracted, a poisoned catalogue is refused, honeypot links
are skipped), and compute the adversarial flags from the graph. The naive path is the
brittle scraper this chapter argues against — class-only parsing that drops drifted
fields, no defense detection so it extracts a poisoned catalogue and follows honeypots,
and no adversarial checks. --selftest runs the market scorer on its own output, naive
versus full, the way Chapter 10's clusterer graded itself.
"""
import argparse
import glob
import json
import os
import sys

import defenses
import graph
import listings
import vendors


def run(corpus_dir, naive=False):
    def body(name):
        return open(os.path.join(corpus_dir, name)).read()

    # listing + vendor records, per page (drift variants included on purpose)
    listing_records, vendor_records = [], []
    for p in sorted(glob.glob(os.path.join(corpus_dir, "listing-*.html"))):
        rec = listings.parse_listing(open(p).read(), naive=naive)
        rec["_file"] = os.path.basename(p)
        listing_records.append(rec)
    for p in sorted(glob.glob(os.path.join(corpus_dir, "vendor-*.html"))):
        rec = vendors.parse_vendor(open(p).read(), naive=naive)
        rec["_file"] = os.path.basename(p)
        vendor_records.append(rec)

    # defense handling — the full pipeline detects; the naive one is blind
    defense_pages = ["wall-captcha.html", "wall-429.html", "catalogue-poisoned.html"]
    status = {"wall-429.html": 429}
    defenses_out, poisoned_extracted = {}, []
    for name in defense_pages:
        if naive:
            cls = {"kind": "ok", "action": "proceed"}      # blind: looks like a page
        else:
            cls = defenses.classify(body(name), status.get(name, 200))
        defenses_out[name] = cls
        # a poisoned catalogue the crawler doesn't recognise gets extracted as real
        if cls["kind"] == "ok" and name == "catalogue-poisoned.html":
            poisoned_extracted.append(name)

    # honeypot links: the full pipeline skips them; the naive one would follow
    hp = defenses.honeypot_links(body("category-hardware.html"))
    honeypots_skipped = [] if naive else hp
    honeypots_followed = hp if naive else []

    flags = ({"resale_rings": [], "borrowed_keys": [], "gamed_reputation": [], "scam_prices": []}
             if naive else graph.build(corpus_dir)["flags"])

    return {
        "listings": listing_records,
        "vendors": vendor_records,
        "defenses": defenses_out,
        "honeypots_skipped": honeypots_skipped,
        "honeypots_followed": honeypots_followed,
        "poisoned_extracted": poisoned_extracted,
        "flags": flags,
    }


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    corpus = os.path.join(here, "corpus")
    sys.path.insert(0, os.path.join(here, "..", "market-scorer"))
    import scorer

    truth = json.load(open(os.path.join(here, "..", "market-scorer", "manifest.json")))
    naive = scorer.score(truth, run(corpus, naive=True))
    full = scorer.score(truth, run(corpus, naive=False))

    ok = True
    # naive scraper: drops drifted fields, catches no adversarial flags, extracts poison
    if not (naive["flag_recall"] == 0.0 and naive["poisoned_extracted"] >= 1
            and naive["record_completeness"] < 1.0):
        print(f"  naive -> {naive}")
        ok = False
    # full pipeline: complete records, all flags, clean collection
    if not (full["record_completeness"] == 1.0 and full["flag_recall"] == 1.0
            and full["defenses_detected"] == full["defenses_total"]
            and full["poisoned_extracted"] == 0):
        print(f"  full -> {full}")
        ok = False
    if not (full["field_recall"] > naive["field_recall"]):
        ok = False

    print(f"selftest: naive completeness {naive['record_completeness']:.2f}, flags {naive['flag_recall']:.2f};")
    print(f"          full completeness {full['record_completeness']:.2f}, flags {full['flag_recall']:.2f}, "
          f"clean collection  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--naive", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.corpus:
        out = run(a.corpus, naive=a.naive)
        if a.summary:
            L, V = out["listings"], out["vendors"]
            req = ("listing_id", "title", "vendor", "category", "price", "ships_from", "ships_to", "terms")
            comp = sum(1 for r in L if all(r.get(k) is not None for k in req))
            f = out["flags"]
            print(f"    listings parsed: {len(L)} ({comp} complete)   vendors parsed: {len(V)}")
            print(f"    flags: rings={f['resale_rings']} borrowed_keys={f['borrowed_keys']} "
                  f"gamed={f['gamed_reputation']} scam={f['scam_prices']}")
            print(f"    poisoned extracted: {len(out['poisoned_extracted'])}   "
                  f"honeypots skipped: {len(out['honeypots_skipped'])}")
            sys.exit(0)
        text = json.dumps(out, indent=2)
        if a.out:
            open(a.out, "w").write(text)
            print(f"wrote {a.out} ({'naive' if a.naive else 'full pipeline'})")
        else:
            print(text)
    else:
        ap.error("use --selftest or --corpus <dir> [--naive] [--out file]")

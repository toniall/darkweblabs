#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Corroborating signals and intent — Chapter 10 (Lab 10.4).

Text and structure can say two pages are alike; they cannot, on their own, say
whether a look-alike is the same operator running a mirror or an adversary running
an impersonation. The reworded clone and a genuinely different service on the same
template score almost identically on shingles and structure — the thing that
separates them is the secondary evidence: do they serve the same asset files, do
they advertise the same payment identity, or has the payment address been swapped?
This module extracts that evidence and turns it into an intent signal. Key material
extraction is reused from the Chapter 9 crawler, so the two artefacts agree on what
a key is.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "crawler"))
from extract import content_hash, extract_keys   # noqa: E402  (reuse Ch9's extractor)

_ASSET_RE = re.compile(r'(?:src|href)=["\']([^"\']*/assets/[^"\']+)["\']', re.I)
_PGP_RE = re.compile(r'\b[0-9A-Z]{14,40}\b')
_BTC_RE = re.compile(r'\bbc1q[a-z0-9_]+\b')


def assets(html):
    """The set of distinct asset references — content-hashed filenames identify the
    actual file, so two pages serving the same file share an asset identity even at
    different hosts."""
    return {a.rsplit("/", 1)[-1] for a in _ASSET_RE.findall(html)}


def shared_assets(html_a, html_b):
    """True if two pages reference at least one identical asset file."""
    return bool(assets(html_a) & assets(html_b))


def keys(html):
    """Identity/payment material a page advertises (reused from the crawler)."""
    return extract_keys(html)


def same_keys(html_a, html_b):
    """Both pages advertise the same payment identity (a same-operator signal)."""
    ka, kb = keys(html_a), keys(html_b)
    return bool(ka.get("btc")) and ka == kb


def payment_swapped(html_canonical, html_member):
    """Both advertise a payment identity and they differ — the impersonation tell."""
    kc, km = keys(html_canonical), keys(html_member)
    if not (kc.get("btc") and km.get("btc")):
        return False
    return kc != km


def keymask_hash(html):
    """Content hash with key material masked — two pages identical apart from swapped
    keys hash the same here, which is how the naive (Chapter 9) clone check works."""
    masked = html
    for m in set(_PGP_RE.findall(html)) | set(_BTC_RE.findall(html)):
        masked = masked.replace(m, "K")
    return content_hash(masked)


def intent(html_canonical, html_member, member_in_directory, text_sim):
    """Classify a look-alike relative to the canonical service.

    mirror  — same operator: shares the canonical's payment identity, or is a
              near-duplicate by text that simply advertises no keys.
    clone   — impersonation: swaps the payment identity, or (a keyless copy whose
              text has been reworded) re-serves the canonical's assets from an
              address the real directory never listed.

    text_sim is the shingle Jaccard to the canonical; it is what tells a benign
    keyless mirror (near-duplicate content) from a reworded keyless clone.
    """
    if same_keys(html_canonical, html_member):
        return "mirror", "shared_payment"
    if payment_swapped(html_canonical, html_member):
        return "clone", "payment_swap"
    if not keys(html_member).get("btc"):
        if text_sim >= 0.5:                       # near-duplicate content, keys just absent
            return "mirror", "benign_copy"
        if shared_assets(html_canonical, html_member) and not member_in_directory:
            return "clone", "keyless_copy"
    return "mirror", "benign_copy"


def selftest():
    ok = True
    here = os.path.dirname(os.path.abspath(__file__))
    C = {n: open(os.path.join(here, "corpus", n)).read()
         for n in ("market.html", "market-mirror-exact.html", "market-clone-keyswap.html",
                   "market-clone-keyless.html", "other-market.html")}

    # exact mirror advertises the same payment identity as the market
    if not same_keys(C["market.html"], C["market-mirror-exact.html"]):
        ok = False
    # the keyswap clone advertises a swapped payment identity
    if not payment_swapped(C["market.html"], C["market-clone-keyswap.html"]):
        ok = False
    # the keyless clone shows no payment identity but re-serves the market's assets
    if keys(C["market-clone-keyless.html"]).get("btc") is not None:
        ok = False
    if not shared_assets(C["market.html"], C["market-clone-keyless.html"]):
        ok = False
    # the different-service trap serves its OWN assets — no overlap with the market
    if shared_assets(C["market.html"], C["other-market.html"]):
        ok = False

    # intent classification on the corpus
    r_swap, _ = intent(C["market.html"], C["market-clone-keyswap.html"], False, 0.86)
    r_keyless, why = intent(C["market.html"], C["market-clone-keyless.html"], False, 0.16)
    r_mirror, _ = intent(C["market.html"], C["market-mirror-exact.html"], False, 1.0)
    if not (r_swap == "clone" and r_keyless == "clone" and why == "keyless_copy"
            and r_mirror == "mirror"):
        print(f"  intent swap={r_swap} keyless={r_keyless}/{why} mirror={r_mirror}")
        ok = False

    print("selftest: shared assets separate a keyless clone from a different site on the")
    print(f"          same template, and payment swap flags impersonation  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

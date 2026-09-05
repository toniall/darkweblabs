#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Near-duplicate detection by shingling — Chapter 10 (Lab 10.2).

Exact hashing says two pages are the same only if every byte matches, so a mirror
that injects one banner looks brand new. Shingling asks a better question: what
fraction of the page's k-word sequences do two pages share? A near-duplicate scores
high; an unrelated page scores low. Jaccard over the full shingle sets is exact and
is what the detector uses; MinHash estimates the same number from a small signature,
which is how this scales to a large crawl. Pure Python, so it self-tests offline.
"""
import argparse
import re
import sys

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def tokens(html):
    """Visible words of a page: tags stripped, lowercased, split on whitespace."""
    text = _TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip().lower()
    return [t for t in text.split(" ") if t]


def shingles(html, k=3):
    """The set of k-word shingles (sliding windows) of a page's text."""
    ws = tokens(html)
    if len(ws) < k:
        return {" ".join(ws)} if ws else set()
    return {" ".join(ws[i:i + k]) for i in range(len(ws) - k + 1)}


def jaccard(a, b):
    """Exact set similarity: |A ∩ B| / |A ∪ B|."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter)


# ---- MinHash: estimate Jaccard from a fixed-size signature (for scale) --------

_MASK = (1 << 61) - 1                      # a Mersenne prime, for hashing mod p


def _perms(num_perm):
    import random
    r = random.Random(1)                   # fixed seed -> deterministic signatures
    return [(r.randrange(1, _MASK), r.randrange(0, _MASK)) for _ in range(num_perm)]


def _h(shingle):
    import hashlib
    return int.from_bytes(hashlib.blake2b(shingle.encode(), digest_size=8).digest(),
                          "big") & _MASK


def minhash(sh, num_perm=64, _cache={}):
    """A MinHash signature: for each permutation, the smallest hashed shingle."""
    perms = _cache.setdefault(num_perm, _perms(num_perm))
    if not sh:
        return [0] * num_perm
    sig = []
    hashed = [_h(s) for s in sh]
    for a, b in perms:
        sig.append(min(((a * hv + b) & _MASK) for hv in hashed))
    return sig


def minhash_sim(sig_a, sig_b):
    """Estimated Jaccard: the fraction of signature positions that agree."""
    if not sig_a or not sig_b:
        return 0.0
    eq = sum(1 for x, y in zip(sig_a, sig_b) if x == y)
    return eq / len(sig_a)


def text_similarity(html_a, html_b, k=3):
    """Exact shingle Jaccard between two pages (what the detector uses)."""
    return jaccard(shingles(html_a, k), shingles(html_b, k))


def selftest():
    ok = True
    base = ("<html><body><h1>The Bazaar</h1><p>vendor NightHawk sealed wallet "
            "ships worldwide escrow held for both parties until release</p></body></html>")
    banner = base.replace("<body>", "<body><div>Mirror synced 2026 bookmark this</div>")
    reworded = ("<html><body><h1>The Bazaar</h1><p>seller NightHawk sealed cold "
                "storage unit global shipping escrow retained for each side</p></body></html>")
    unrelated = ("<html><body><h1>The Commons</h1><ul><li>opsec threads</li>"
                 "<li>which escrow do you trust</li></ul></body></html>")

    sb = shingles(base)
    # a one-banner near-duplicate stays very close; unrelated is far
    j_banner = text_similarity(base, banner)
    j_reword = text_similarity(base, reworded)
    j_unrel = text_similarity(base, unrelated)
    # the banner mirror stays close; rewording defeats shingling (motivating structure,
    # Lab 10.3); an unrelated page is far
    if not (j_banner > 0.7 and j_reword < 0.30 and j_unrel < 0.15 and j_banner > j_reword):
        print(f"  jaccard banner={j_banner:.2f} reword={j_reword:.2f} unrel={j_unrel:.2f}")
        ok = False

    # MinHash estimates Jaccard: same page -> 1.0, and tracks the exact ordering
    if minhash_sim(minhash(sb), minhash(sb)) != 1.0:
        ok = False
    mb = minhash_sim(minhash(sb), minhash(shingles(banner)))
    mu = minhash_sim(minhash(sb), minhash(shingles(unrelated)))
    if not (mb > mu):
        print(f"  minhash banner={mb:.2f} unrel={mu:.2f}")
        ok = False

    print("selftest: shingle Jaccard separates near-duplicates from unrelated pages,")
    print(f"          and MinHash estimates it from a signature  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

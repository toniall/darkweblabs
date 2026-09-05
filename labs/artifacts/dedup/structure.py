#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Structural fingerprinting — Chapter 10 (Lab 10.3).

Shingling fails when a clone rewrites the text, because the words move even though
the page is the same shape. Structural fingerprinting reads only the shape: the
sequence of HTML tags, with text and attributes thrown away. A clone that copies a
site's template scores a near-identical structural fingerprint no matter how much
copy it rewrites. SimHash turns that tag skeleton into a 64-bit fingerprint whose
Hamming distance measures structural difference. Crucially, structure alone cannot
tell a clone from a different service built on the same template — that separation
needs the corroborating signals of Lab 10.4.
"""
import argparse
import hashlib
import re
import sys

_TAG_RE = re.compile(r"<\s*([a-zA-Z][a-zA-Z0-9]*)")


def skeleton(html):
    """The ordered sequence of opening tag names — the page's shape, no content."""
    return [t.lower() for t in _TAG_RE.findall(html)]


def _features(html):
    """Tag trigrams of the skeleton, so order and nesting shape the fingerprint."""
    sk = skeleton(html)
    if len(sk) < 3:
        return ["|".join(sk)] if sk else []
    return ["|".join(sk[i:i + 3]) for i in range(len(sk) - 2)]


def _hash(feature, bits=64):
    d = hashlib.blake2b(feature.encode(), digest_size=bits // 8).digest()
    return int.from_bytes(d, "big")


def simhash(html, bits=64):
    """A 64-bit SimHash of the page's structural features."""
    feats = _features(html)
    if not feats:
        return 0
    v = [0] * bits
    for f in feats:
        h = _hash(f, bits)
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(bits):
        if v[i] > 0:
            out |= (1 << i)
    return out


def hamming(a, b):
    return bin(a ^ b).count("1")


def structure_sim(html_a, html_b, bits=64):
    """1.0 = identical structure, 0.0 = maximally different (Hamming over the fingerprint)."""
    return 1.0 - hamming(simhash(html_a, bits), simhash(html_b, bits)) / bits


def selftest():
    ok = True
    tmpl = ("<html><head><link><title>t</title></head><body><header><img><h1>{h}</h1>"
            "<nav><a>a</a><a>b</a></nav></header><main><table><tbody>"
            "<tr><td>{a}</td><td>{b}</td></tr><tr><td>{c}</td><td>{d}</td></tr>"
            "</tbody></table></main></body></html>")
    market = tmpl.format(h="Bazaar", a="NightHawk", b="wallet", c="GreyOwl", d="phone")
    # reworded content, SAME template -> structure near-identical
    reworded = tmpl.format(h="Bazaar", a="seller unit", b="global", c="handset", d="EU")
    # a different service on the SAME template -> ALSO near-identical (the trap)
    other = tmpl.format(h="Reef", a="BlueReef", b="coral", c="Cobbler", d="boots")
    # a genuinely different template
    forum = ("<html><head><title>f</title></head><body><header><h1>Commons</h1></header>"
             "<main><ul><li><a>x</a></li><li><a>y</a></li></ul></main></body></html>")

    s_reword = structure_sim(market, reworded)
    s_other = structure_sim(market, other)
    s_forum = structure_sim(market, forum)
    # the reworded clone matches structurally; so does the trap; the forum does not
    if not (s_reword > 0.9 and s_other > 0.9 and s_forum < 0.8 and s_reword > s_forum):
        print(f"  structure_sim reword={s_reword:.2f} other={s_other:.2f} forum={s_forum:.2f}")
        ok = False
    # identical pages are identical
    if structure_sim(market, market) != 1.0:
        ok = False

    print("selftest: structural SimHash matches a reworded clone by template — and also a")
    print(f"          different site on the same template (needs 10.4)  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Stylometric similarity — Chapter 13 (Lab 13.3).

Keys and wallets can be rotated; a writing voice is harder to change and easier to forget
to change. Stylometry fingerprints how a persona writes — the frequencies of its function
words and its character trigrams — and compares fingerprints to re-link an operator that
rotated its hard identifiers but kept its register. It is a SOFT signal on purpose: it
corroborates, it does not prove. It is foolable (a careful operator can mimic a voice or
launder its own through translation) and biased (short samples and second-language writers
skew it), so a stylometric match raises confidence in a link but never establishes one by
itself. The fusion in Lab 13.5 treats it accordingly.
"""
import argparse
import math
import os
import re
import sys

import identifiers

FUNCTION_WORDS = [
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "as",
    "at", "by", "we", "i", "you", "u", "it", "is", "are", "was", "will", "shall", "would",
    "just", "so", "ok", "please", "kindly", "hence", "moreover", "whilst", "thus", "step",
    "no", "not", "do", "dont", "your", "our", "my", "this", "that", "here", "heres",
    "thats", "gonna", "wanna", "once", "every", "any", "will", "if", "then", "them",
]


def _words(text):
    return re.findall(r"[a-z']+", text.lower())


def _fw_vec(text):
    words = _words(text)
    n = len(words) or 1
    counts = {fw: 0 for fw in FUNCTION_WORDS}
    for w in words:
        if w in counts:
            counts[w] += 1
    return {fw: c / n for fw, c in counts.items()}


def _tri_vec(text):
    s = re.sub(r"\s+", " ", text.lower())
    tris = {}
    for i in range(len(s) - 2):
        t = s[i:i + 3]
        tris[t] = tris.get(t, 0) + 1
    n = sum(tris.values()) or 1
    return {t: c / n for t, c in tris.items()}


def _cos(a, b):
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def fingerprint(text):
    return {"fw": _fw_vec(text), "tri": _tri_vec(text)}


def similarity(fa, fb):
    return round(0.5 * _cos(fa["fw"], fb["fw"]) + 0.5 * _cos(fa["tri"], fb["tri"]), 3)


def matrix(personas):
    fps = {h: fingerprint(r["posts"]) for h, r in personas.items()}
    out = {}
    hs = sorted(fps)
    for i, a in enumerate(hs):
        for b in hs[i + 1:]:
            out[(a, b)] = similarity(fps[a], fps[b])
    return out


def style_links(personas, threshold):
    return [{"a": a, "b": b, "signal": "stylometry", "weight": 0.6, "sim": sim}
            for (a, b), sim in matrix(personas).items() if sim >= threshold]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--matrix", action="store_true")
    a = ap.parse_args()
    P = identifiers.load(a.corpus)
    m = matrix(P)
    for (x, y), sim in sorted(m.items(), key=lambda kv: -kv[1]):
        print(f"    {sim:.3f}  {x:12} {y}")

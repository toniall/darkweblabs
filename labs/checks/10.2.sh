#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.2 — Shingling and MinHash
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
DEDUP="$HERE/../artifacts/dedup"
echo; echo "Lab 10.2 — Shingling and MinHash"; echo
ck "shingle.py self-test passes" 'python3 "$DEDUP/shingle.py" --selftest'
ck "shingles + Jaccard are implemented" 'grep -q "def shingles" "$DEDUP/shingle.py" && grep -q "def jaccard" "$DEDUP/shingle.py"'
ck "a MinHash signature and similarity are implemented" 'grep -q "def minhash" "$DEDUP/shingle.py" && grep -q "def minhash_sim" "$DEDUP/shingle.py"'
ck "text_similarity is exposed for the clusterer" 'grep -q "def text_similarity" "$DEDUP/shingle.py"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

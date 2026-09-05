#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.3 — Structural fingerprinting
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
DEDUP="$HERE/../artifacts/dedup"
echo; echo "Lab 10.3 — Structural fingerprinting"; echo
ck "structure.py self-test passes" 'python3 "$DEDUP/structure.py" --selftest'
ck "the DOM skeleton is extracted" 'grep -q "def skeleton" "$DEDUP/structure.py"'
ck "SimHash + Hamming distance are implemented" 'grep -q "def simhash" "$DEDUP/structure.py" && grep -q "def hamming" "$DEDUP/structure.py"'
ck "structure_sim is exposed for the clusterer" 'grep -q "def structure_sim" "$DEDUP/structure.py"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

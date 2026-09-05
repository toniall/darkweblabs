#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.7 — Scoring the detector and closing the loop
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
SCORER="$HERE/../artifacts/dedup-scorer"
FULL="$("$LAB" dedup score 2>/dev/null)"
NAIVE="$("$LAB" dedup score --naive 2>/dev/null)"
echo; echo "Lab 10.7 — Scoring the detector and closing the loop"; echo
ck "the dedup scorer self-test passes" 'python3 "$SCORER/scorer.py" --selftest'
ck "full engine: mirror AND clone recall both 1.00" '[ "$(grep -Ec "recall +1.00" <<< "$FULL")" -eq 2 ]'
ck "full engine: clone precision 1.00" 'grep -Eq "precision 1.00" <<< "$FULL"'
ck "full engine: zero false merges" 'grep -Eq "false merges +0" <<< "$FULL"'
ck "full engine beats the naive baseline (0.33 -> 1.00 on mirrors)" 'grep -Eq "recall +0.33" <<< "$NAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

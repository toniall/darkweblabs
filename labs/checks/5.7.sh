#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.7 — A threat model that has weights
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
WS="$HERE/../artifacts/threat-model/worksheet.md"
echo; echo "Lab 5.7 — A threat model that has weights"; echo
ck "the worksheet ships with adversaries and attacks pre-listed" \
   "test -f '$WS' && grep -qi 'canary' '$WS' && grep -qi 'guard discovery' '$WS' && grep -qi 'correlation' '$WS'"
ck "it leaves the weight column to be filled (L x I x E)" \
   "grep -qi 'L x I x E' '$WS'"
ck "controls the model relies on still hold — fails closed (2.7)" \
   "bash '$HERE/2.7.sh'"
ck "controls the model relies on still hold — guard persists (3.3)" \
   "bash '$HERE/3.3.sh'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

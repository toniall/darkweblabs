#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.2 — The evidence chain
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
EV="$($LAB capstone evidence 2>&1)"
echo; echo "Lab 15.2 — The evidence chain"; echo
ck "the graph names the target operator, keyed by the reused signed key" 'grep -E "operator: Alpha" <<< "$EV" && grep -E "F19B7A0C4E82D5613FA0" <<< "$EV"'
ck "the high-confidence cluster carries all four personas" 'grep -E "BlackVault, NightHawk, RedLattice, n1ghthawk" <<< "$EV" && grep -E "\[high\]" <<< "$EV"'
ck "leak facets — bluffed victims and a publication — are present" 'grep -E "bluffed victims" <<< "$EV" && grep -E "Meridian Health" <<< "$EV"'
ck "detection facets and the Mimic framing flag are present" 'grep -E "resurface n1ghthawk2" <<< "$EV" && grep -E "clone NightHawkMkt-x" <<< "$EV" && grep -E "Mimic" <<< "$EV"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

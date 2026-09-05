#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.3 — Classifying events
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
CL="$($LAB detect classify 2>&1)"
echo; echo "Lab 14.3 — Classifying events"; echo
ck "all 22 raw changes are typed" 'grep -E "typed events: 22" <<< "$CL"'
ck "the ten banner flips are cosmetic_churn" 'grep -E "10[[:space:]]+cosmetic_churn" <<< "$CL"'
ck "the impersonating look-alike is typed new_clone" 'grep -E "new_clone +NightHawkMkt-x" <<< "$CL"'
ck "the resurfacing persona is typed operator_resurface" 'grep -E "operator_resurface +n1ghthawk2" <<< "$CL"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

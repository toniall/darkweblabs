#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.6 — Noise, drift, and the flood
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
MON="$($LAB detect monitor 2>&1)"
NAIVE="$($LAB detect monitor --naive 2>&1)"
echo; echo "Lab 14.6 — Noise, drift, and the flood"; echo
ck "the full monitor emits 8 ranked alerts" 'grep -E "full monitor: 8 alerts" <<< "$MON"'
ck "it suppresses 10 churn and collapses 4 duplicates" 'grep -E "suppressed 10 churn, collapsed 4 duplicates" <<< "$MON"'
ck "the naive monitor emits 22 flat alerts" 'grep -E "naive monitor: 22 alerts" <<< "$NAIVE"'
ck "both monitors catch the two criticals (recall is not the differentiator)" 'grep -E "new_clone" <<< "$MON" && grep -E "operator_resurface" <<< "$MON" && grep -E "new_clone" <<< "$NAIVE" && grep -E "operator_resurface" <<< "$NAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

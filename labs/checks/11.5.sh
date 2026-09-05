#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.5 — The vendor and reputation graph
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/market-extract"
GRAPH="$("$LAB" market graph 2>/dev/null)"
echo; echo "Lab 11.5 — The vendor and reputation graph"; echo
ck "vendor graph self-tests (rings, prolific, reputation)" '( cd "$ART" && python3 graph.py --selftest )'
ck "NightHawk is the prolific vendor with two listings" 'grep -Eq "NightHawk., 2" <<< "$GRAPH"'
ck "the resale ring is listings 1001 and 1006" 'grep -Eq "resale rings:.*1001, 1006" <<< "$GRAPH"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.3 — Confidence and calibration
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
CL="$($LAB capstone claims 2>&1)"
echo; echo "Lab 15.3 — Confidence and calibration"; echo
ck "the timezone claim is low (a single soft signal)" 'grep -E "low +assessment\] timezone" <<< "$CL"'
ck "the rebrand claim is moderate (indirect signals)" 'grep -E "moderate assessment\] rebrand" <<< "$CL"'
ck "the identity claim is high, held by a hard identifier" 'grep -E "high +assessment\] identity" <<< "$CL"'
ck "every claim cites its source engine" 'test $(grep -Ec "<- (persona-linkage|leak-negotiation|detection)/" <<< "$CL") -ge 8'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.1 — The intelligence product
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
SELF="$($LAB capstone selftest 2>&1)"
echo; echo "Lab 15.1 — The intelligence product"; echo
ck "the capstone engine self-tests pass offline" 'grep -E "capstone self-tests passed" <<< "$SELF"'
ck "the four engines run and assemble into one evidence graph" 'grep -E "four engines run and assemble" <<< "$SELF"'
ck "eight claims are built with a calibrated confidence" 'grep -E "8 claims built from the graph" <<< "$SELF"'
ck "the full report is sourced and calibrated while the naive assembler overclaims" 'grep -E "naive provenance 0.00/overclaims 6" <<< "$SELF"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

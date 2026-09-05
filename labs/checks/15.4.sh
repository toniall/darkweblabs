#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.4 — Assembling the report
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
REP="$($LAB capstone report 2>&1)"
echo; echo "Lab 15.4 — Assembling the report"; echo
ck "the report leads with a bottom line up front" 'grep -E "^BLUF:" <<< "$REP"'
ck "findings are tagged with type and confidence" 'grep -E "\[assessment/high" <<< "$REP" && grep -E "\[fact/high" <<< "$REP"'
ck "findings cite their source engine" 'grep -E "source: persona-linkage/fuse" <<< "$REP"'
ck "the report carries an evidence annex and an attribution boundary" 'grep -E "EVIDENCE ANNEX:" <<< "$REP" && grep -E "ATTRIBUTION BOUNDARY:" <<< "$REP"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

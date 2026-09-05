#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.5 — Analytic integrity and the overclaim trap
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
NREP="$($LAB capstone report --naive 2>&1)"
G="$($LAB capstone grade 2>&1)"
GN="$($LAB capstone grade --naive 2>&1)"
echo; echo "Lab 15.5 — Analytic integrity and the overclaim trap"; echo
ck "the naive report flattens every finding to fact (no assessments, no sources)" 'grep -E "\[fact/high" <<< "$NREP" && ! grep -E "assessment" <<< "$NREP"'
ck "the naive report states it drops sourcing, falsifiers, and boundary" 'grep -E "no sourcing" <<< "$NREP"'
ck "the naive report scores 0.00 provenance and 6 overclaims" 'grep -E "provenance complete +0 / 8" <<< "$GN" && grep -E "overclaims +6" <<< "$GN"'
ck "the full report scores 1.00 provenance and 0 overclaims on the same findings" 'grep -E "provenance complete +8 / 8" <<< "$G" && grep -E "overclaims +0" <<< "$G"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

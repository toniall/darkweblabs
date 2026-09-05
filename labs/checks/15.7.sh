#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.7 — Scoring the report and the book's close
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
G="$($LAB capstone grade 2>&1)"
GN="$($LAB capstone grade --naive 2>&1)"
echo; echo "Lab 15.7 — Scoring the report and the book's close"; echo
ck "the full report scores 8/8 coverage, provenance, and calibration" 'grep -E "claim coverage +8 / 8" <<< "$G" && grep -E "provenance complete +8 / 8" <<< "$G" && grep -E "calibration +8 / 8" <<< "$G"'
ck "the full report has zero overclaims" 'grep -E "overclaims +0" <<< "$G"'
ck "the naive report has the same coverage but 0.25 calibration and 6 overclaims" 'grep -E "claim coverage +8 / 8" <<< "$GN" && grep -E "calibration +2 / 8" <<< "$GN" && grep -E "overclaims +6" <<< "$GN"'
ck "the naive report strips all provenance (0.00)" 'grep -E "provenance complete +0 / 8" <<< "$GN"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

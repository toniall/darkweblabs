#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.7 — Scoring, calibration, and where linkage stops
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
FSC="$($LAB link score 2>&1)"
NSC="$($LAB link score --naive 2>&1)"
echo; echo "Lab 13.7 — Scoring, calibration, and where linkage stops"; echo
ck "full linker recovers every true link (recall 7/7)" 'grep -E "link recall .*7 / 7" <<< "$FSC"'
ck "full linker draws no false merge (0) and flags all borrowed-key pairs (4/4)" 'grep -E "false merges .*0 " <<< "$FSC" && grep -E "framing flagged .*4 / 4" <<< "$FSC"'
ck "naive precision collapses (6/15) with nine false merges" 'grep -E "link precision .*6 / 15" <<< "$NSC" && grep -E "false merges .*9 " <<< "$NSC"'
ck "naive fails calibration and flags no framing (0/2, 0/4)" 'grep -E "confidence calibration 0 / 2" <<< "$NSC" && grep -E "framing flagged .*0 / 4" <<< "$NSC"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

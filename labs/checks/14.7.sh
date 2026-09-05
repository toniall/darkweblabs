#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.7 — Scoring the detector and the watch loop
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
G="$($LAB detect grade 2>&1)"
GN="$($LAB detect grade --naive 2>&1)"
echo; echo "Lab 14.7 — Scoring the detector and the watch loop"; echo
ck "full monitor scores 8/8 recall and 8/8 precision" 'grep -E "alert recall +8 / 8 +1.00" <<< "$G" && grep -E "alert precision +8 / 8 +1.00" <<< "$G"'
ck "full monitor has zero false alerts and surfaces 2/2 criticals" 'grep -E "false alerts +0 " <<< "$G" && grep -E "criticals surfaced +2 / 2" <<< "$G"'
ck "naive precision collapses to 0.36 with 12 false alerts" 'grep -E "0.36" <<< "$GN" && grep -E "false alerts +12 " <<< "$GN"'
ck "naive surfaces 0/2 criticals — the crying-wolf failure" 'grep -E "criticals surfaced +0 / 2" <<< "$GN"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

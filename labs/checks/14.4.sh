#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.4 — Scoring and prioritization
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
SC="$($LAB detect score 2>&1)"
echo; echo "Lab 14.4 — Scoring and prioritization"; echo
ck "both criticals score critical" 'test $(grep -Ec "^ *critical " <<< "$SC") -ge 2'
ck "the watched market going dark is boosted to high" 'grep -E "high +market_down +NightHawkMkt.*watched" <<< "$SC"'
ck "the resurface is a watched critical" 'grep -E "critical +operator_resurface +n1ghthawk2.*watched" <<< "$SC"'
ck "cosmetic churn is scored suppress" 'grep -E "suppress +cosmetic_churn" <<< "$SC"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

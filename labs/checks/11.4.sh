#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.4 — Sessions at scale, and the shadow-ban
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/market-extract"
SCAN="$( cd "$ART" && python3 defenses.py --scan corpus 2>/dev/null )"
SNAIVE="$("$LAB" market score --naive 2>/dev/null)"
SFULL="$("$LAB" market score 2>/dev/null)"
echo; echo "Lab 11.4 — Sessions at scale, and the shadow-ban"; echo
ck "poisoned catalogue classified as degraded and skipped" 'grep -Eq "poisoned.*skip" <<< "$SCAN"'
ck "naive scraper on a flagged session extracts the poison (count 1)" 'grep -Eq "poisoned extracted  1" <<< "$SNAIVE"'
ck "full pipeline refuses the poison (count 0)" 'grep -Eq "poisoned extracted  0" <<< "$SFULL"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

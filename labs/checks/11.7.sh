#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.7 — Scoring extraction, and closing the loop
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
SCO="$HERE/../artifacts/market-scorer"
SFULL="$("$LAB" market score 2>/dev/null)"
SNAIVE="$("$LAB" market score --naive 2>/dev/null)"
echo; echo "Lab 11.7 — Scoring extraction, and closing the loop"; echo
ck "market scorer self-tests" '( cd "$SCO" && python3 scorer.py --selftest )'
ck "full extractor: field recall 88/88" 'grep -Eq "field recall +88 / 88" <<< "$SFULL"'
ck "full extractor: all 4 adversarial flags caught" 'grep -Eq "adversarial flags +4 / 4" <<< "$SFULL"'
ck "full extractor refuses the poison (0)" 'grep -Eq "poisoned extracted  0" <<< "$SFULL"'
ck "naive baseline: field recall 81/88" 'grep -Eq "field recall +81 / 88" <<< "$SNAIVE"'
ck "naive baseline: 0 adversarial flags caught" 'grep -Eq "adversarial flags +0 / 4" <<< "$SNAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

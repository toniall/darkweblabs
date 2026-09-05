#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.2 — Structured extraction: pages to records
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/market-extract"
FULL="$("$LAB" market extract 2>/dev/null)"
NAIVE="$("$LAB" market extract --naive 2>/dev/null)"
echo; echo "Lab 11.2 — Structured extraction: pages to records"; echo
ck "listing parser self-tests (typed records, drift resilience)" '( cd "$ART" && python3 listings.py --selftest )'
ck "vendor parser self-tests (handle/pgp/rating/join/feedback)" '( cd "$ART" && python3 vendors.py --selftest )'
ck "full pipeline completes all 7 listings" 'grep -Eq "listings parsed: 7 [(]7 complete[)]" <<< "$FULL"'
ck "naive scraper drops the drifted listing (6 complete)" 'grep -Eq "listings parsed: 7 [(]6 complete[)]" <<< "$NAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

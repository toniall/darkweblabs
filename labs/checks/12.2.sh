#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.2 — Leak-site victim extraction
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/leak-extract"
E="$("$LAB" leak extract 2>/dev/null)"
EN="$("$LAB" leak extract --naive 2>/dev/null)"
SC="$("$LAB" leak score 2>/dev/null)"
echo; echo "Lab 12.2 — Leak-site victim extraction"; echo
ck "victims.py self-tests (record + drift resilience)" '( cd "$ART" && python3 victims.py --selftest )'
ck "full extraction: 6 victims parse, all complete" 'grep -Eq "victims parsed: 6 .6 complete." <<< "$E"'
ck "naive class-only read drops the drift entry to 5 complete" 'grep -Eq "victims parsed: 6 .5 complete." <<< "$EN"'
ck "full victim field recall 48/48 (1TB normalised to GB)" 'grep -Eq "victim field recall +48 / 48" <<< "$SC"'
ck "full record completeness 6/6" 'grep -Eq "record completeness +6 / 6" <<< "$SC"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

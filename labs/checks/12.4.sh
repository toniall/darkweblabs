#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.4 — Reposted victims and affiliate movement
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/leak-extract"
R="$("$LAB" leak reposts 2>/dev/null)"
echo; echo "Lab 12.4 — Reposted victims and affiliate movement"; echo
ck "reposts.py self-tests (mirror vs clone)" '( cd "$ART" && python3 reposts.py --selftest )'
ck "Apex reposted with the same claim is a mirror (affiliate)" 'grep -Eq "Apex.*mirror" <<< "$R"'
ck "GraniteWorks reposted inflated is a clone (recycled)" 'grep -Eq "GraniteWorks.*clone" <<< "$R"'
ck "the clone claim grew 50 -> 150 GB" 'grep -Eq "50.0 vs 150.0" <<< "$R"'
ck "the mirror claim held (1000 vs 1000 GB)" 'grep -Eq "1000.0 vs 1000.0" <<< "$R"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

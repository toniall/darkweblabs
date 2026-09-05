#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.3 — The victim lifecycle over time
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/leak-extract"
L="$("$LAB" leak lifecycle 2>/dev/null)"
echo; echo "Lab 12.3 — The victim lifecycle over time"; echo
ck "lifecycle.py self-tests (snapshot diff)" '( cd "$ART" && python3 lifecycle.py --selftest )'
ck "1001's deadline slid later — countdown theatre" 'grep -Eq "slid deadlines.*1001" <<< "$L"'
ck "1002 classified as published" 'grep -Eq "published: +.1002." <<< "$L"'
ck "1003 classified as a quiet withdrawal" 'grep -Eq "withdrawn.*1003" <<< "$L"'
ck "1005 classified as escalated (teased -> countdown)" 'grep -Eq "escalated: +.1005." <<< "$L"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

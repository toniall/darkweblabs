#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.1 — The linkage problem and the identifier ledger
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/persona-extract"
CORPUS="$ART/corpus"
LEDGER="$($LAB link ledger 2>&1)"
SELF="$($LAB link selftest 2>&1)"
echo; echo "Lab 13.1 — The linkage problem and the identifier ledger"; echo
ck "corpus holds 8 persona profiles across surfaces" '[ "$(ls "$CORPUS"/persona-*.txt 2>/dev/null | wc -l)" -eq 8 ]'
ck "every profile carries the synthetic watermark" '[ "$(grep -lF "SYNTHETIC LAB DATA — persona profile" "$CORPUS"/persona-*.txt | wc -l)" -eq 8 ]'
ck "the linkage engine self-tests offline (all modules + scorer)" 'grep -Fq "link self-tests passed" <<< "$SELF"'
ck "ledger shows a persona whose signed key differs from its displayed key" 'grep -E "Mimic .*signs:CC11DD22EE33FF445566 .*shows:F19B7A0C4E82D5613FA0" <<< "$LEDGER"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.1 — The market as a database, and a page store
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/market-extract"
SELF="$("$LAB" market selftest 2>/dev/null)"
STORE="$("$LAB" market store 2>/dev/null)"
echo; echo "Lab 11.1 — The market as a database, and a page store"; echo
ck "market-lab corpus present (>=19 pages)" '[ "$(ls "$ART/corpus"/*.html 2>/dev/null | wc -l)" -ge 19 ]'
ck "every corpus page carries the synthetic watermark" '[ -z "$(grep -L "SYNTHETIC LAB DATA" "$ART/corpus"/*.html)" ]'
ck "market selftest passes offline (store/listings/vendors/defenses/graph/scorer)" 'grep -q "market self-tests passed" <<< "$SELF"'
ck "store ingests 19 fetched pages into 18 objects" 'grep -Eq "19 fetched pages -> 18 distinct objects" <<< "$STORE"'
ck "the byte-identical mirror collapses at storage" 'grep -q "byte-identical mirror collapsed at storage" <<< "$STORE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

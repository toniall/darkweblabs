#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.1 — Where exact hashing fails
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
DEDUP="$HERE/../artifacts/dedup"
CORPUS="$DEDUP/corpus"
NAIVE="$("$LAB" dedup score --naive 2>/dev/null)"
echo; echo "Lab 10.1 — Where exact hashing fails"; echo
ck "clone-lab corpus present (9 pages)" '[ "$(ls "$CORPUS"/*.html 2>/dev/null | wc -l)" -eq 9 ]'
ck "every corpus page carries the synthetic watermark" '[ "$(grep -l "SYNTHETIC LAB DATA" "$CORPUS"/*.html 2>/dev/null | wc -l)" -eq 9 ]'
ck "the hard cases exist: banner mirror, keyswap clone, keyless clone, decoy" '[ -f "$CORPUS/market-mirror-banner.html" ] && [ -f "$CORPUS/market-clone-keyswap.html" ] && [ -f "$CORPUS/market-clone-keyless.html" ] && [ -f "$CORPUS/other-market.html" ]'
ck "dedup self-tests pass offline (shingle, structure, signals, cluster+scorer)" '"$LAB" dedup selftest'
ck "naive detector scores mirror recall 0.33" 'grep -Eq "recall +0.33" <<< "$NAIVE"'
ck "naive detector scores clone recall 0.50" 'grep -Eq "recall +0.50" <<< "$NAIVE"'
ck "naive detector still makes no false merges" 'grep -Eq "false merges +0" <<< "$NAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

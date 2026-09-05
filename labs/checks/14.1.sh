#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.1 — The monitoring shift and the watchlist
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/detect-monitor"
SELF="$($LAB detect selftest 2>&1)"
WL="$($LAB detect watchlist 2>&1)"
echo; echo "Lab 14.1 — The monitoring shift and the watchlist"; echo
ck "the detect-lab ships three watermarked monitoring snapshots" 'test $(ls "$ART"/corpus/snapshot-t*.txt 2>/dev/null | wc -l) -eq 3 && grep -q "SYNTHETIC LAB DATA" "$ART"/corpus/snapshot-t1.txt'
ck "the detection engine self-tests pass offline" 'grep -E "detect self-tests passed" <<< "$SELF"'
ck "the watchlist carries the watched key F19B7A0C" 'grep -E "F19B7A0C4E82D5613FA0" <<< "$WL"'
ck "the watchlist is Chapter 13 Alpha (NightHawk + RedLattice)" 'grep -E "NightHawk" <<< "$WL" && grep -E "RedLattice" <<< "$WL"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.5 — Correlation and dedup
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
CO="$($LAB detect correlate 2>&1)"
MON="$($LAB detect monitor 2>&1)"
echo; echo "Lab 14.5 — Correlation and dedup"; echo
ck "four cross-surface duplicates are collapsed" 'grep -E "collapsed 4 " <<< "$CO"'
ck "eighteen events remain after dedup" 'grep -E "18 events remain" <<< "$CO"'
ck "the origin deadline_slip survives, not the mirror artifact" 'grep -E "deadline_slip +Northwind +@RedLattice" <<< "$MON" && ! grep -E "new_victim +Northwind" <<< "$MON"'
ck "the new_mirror alert survives correlation" 'grep -E "new_mirror +RedLattice-m1" <<< "$MON"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

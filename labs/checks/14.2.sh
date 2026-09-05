#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.2 — The change feed
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
FEED="$($LAB detect feed 2>&1)"
echo; echo "Lab 14.2 — The change feed"; echo
ck "the raw feed diffs the timeline into 22 events" 'grep -E "raw events: 22" <<< "$FEED"'
ck "cosmetic churn pages appear as raw diffs" 'test $(grep -Ec "page +churn-" <<< "$FEED") -ge 8'
ck "the byte-identical mirror re-lists victims on its own surface" 'grep -E "@RedLattice-m1" <<< "$FEED"'
ck "the resurfacing persona appears in the feed at t3" 'grep -E "persona +n1ghthawk2" <<< "$FEED"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

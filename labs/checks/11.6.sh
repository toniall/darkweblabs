#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.6 — The data is adversarial
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
GRAPH="$("$LAB" market graph 2>/dev/null)"
echo; echo "Lab 11.6 — The data is adversarial"; echo
ck "bait price flagged: listing 1005 below category median" 'grep -Eq "bait prices:.*1005" <<< "$GRAPH"'
ck "borrowed key flagged: Mimic shares NightHawk fingerprint" 'grep -Eq "borrowed keys:.*Mimic.*NightHawk" <<< "$GRAPH"'
ck "gamed reputation flagged: SaltMine feedback velocity" 'grep -Eq "gamed reputation:.*SaltMine" <<< "$GRAPH"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

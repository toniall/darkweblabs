#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.3 — Stylometry, a soft signal
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
STYLE="$($LAB link style 2>&1)"
echo; echo "Lab 13.3 — Stylometry, a soft signal"; echo
ck "within-operator handle-transform pair scores high (NightHawk/n1ghthawk 0.775)" 'grep -E "0.775 .*NightHawk .*n1ghthawk" <<< "$STYLE"'
ck "key-rotating operator's personas link by voice (IronVault/SaltMine 0.617)" 'grep -E "0.617 .*IronVault .*SaltMine" <<< "$STYLE"'
ck "cross-operator pair scores well below the threshold (Mimic/NightHawk 0.340)" 'grep -E "0.340 .*Mimic .*NightHawk" <<< "$STYLE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

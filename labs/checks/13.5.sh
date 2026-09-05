#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.5 — Fusing the signals into an operator
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
FUSE="$($LAB link fuse 2>&1)"
echo; echo "Lab 13.5 — Fusing the signals into an operator"; echo
ck "operator recovered at HIGH confidence with all four personas" 'grep -E "HIGH.*BlackVault, NightHawk, RedLattice, n1ghthawk" <<< "$FUSE"'
ck "key-rotating operator recovered at medium confidence (soft only)" 'grep -E "medium. .*IronVault, SaltMine" <<< "$FUSE"'
ck "the frame and the look-alike stay singletons (Mimic, Nighthawke)" 'grep -E "single.*Mimic$" <<< "$FUSE" && grep -E "single.*Nighthawke$" <<< "$FUSE"'
ck "the borrowed key raises exactly four framing flags" '[ "$(grep -Ec "possible framing" <<< "$FUSE")" -eq 4 ]'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

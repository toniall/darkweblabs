#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.4 — Rhythm, handles, and tactic signatures
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
BEH="$($LAB link behavior 2>&1)"
echo; echo "Lab 13.4 — Rhythm, handles, and tactic signatures"; echo
ck "handle transform matches the leet variant (NightHawk/n1ghthawk)" 'grep -E "handle_transform .*NightHawk .*n1ghthawk" <<< "$BEH"'
ck "shared activity rhythm links the key-rotating pair (IronVault/SaltMine)" 'grep -E "rhythm .*IronVault .*SaltMine" <<< "$BEH"'
ck "repeated tactic sequence corroborates the two leak brands (RedLattice/BlackVault)" 'grep -E "tactic_sequence .*BlackVault .*RedLattice" <<< "$BEH"'
ck "the one-edit look-alike is NOT reported as a handle transform" '! grep -E "handle_transform .*Nighthawke" <<< "$BEH"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

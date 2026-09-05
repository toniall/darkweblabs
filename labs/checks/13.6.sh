#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.6 — The adversarial identity
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
NFUSE="$($LAB link fuse --naive 2>&1)"
FUSE="$($LAB link fuse 2>&1)"
echo; echo "Lab 13.6 — The adversarial identity"; echo
ck "naive over-merges the frame and the look-alike into the operator" 'grep -E "Mimic, NightHawk, Nighthawke" <<< "$NFUSE"'
ck "naive splits the key-rotating operator into singletons" 'grep -E "single.*IronVault$" <<< "$NFUSE" && grep -E "single.*SaltMine$" <<< "$NFUSE"'
ck "full linker keeps the operator intact and the frame apart" 'grep -E "HIGH.*BlackVault, NightHawk, RedLattice, n1ghthawk" <<< "$FUSE"'
ck "full linker recovers the key-rotating operator naive split" 'grep -E "medium. .*IronVault, SaltMine" <<< "$FUSE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

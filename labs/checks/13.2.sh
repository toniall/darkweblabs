#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 13.2 — Hard identifiers and the provenance trap
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
HARD="$($LAB link hard 2>&1)"
NAIVE="$($LAB link fuse --naive 2>&1)"
echo; echo "Lab 13.2 — Hard identifiers and the provenance trap"; echo
ck "operator personas share a signed key (NightHawk/RedLattice)" 'grep -E "shared_signed_key .*NightHawk .*RedLattice" <<< "$HARD"'
ck "operator personas share a wallet (NightHawk/RedLattice)" 'grep -E "shared_wallet .*NightHawk .*RedLattice" <<< "$HARD"'
ck "borrowed displayed-only key is flagged as framing, not linked (Mimic)" 'grep -E "framing. Mimic .*NightHawk" <<< "$HARD"'
ck "naive linker instead treats the same pair as a shared identifier" 'grep -Fq "shared_identifier" <<< "$NAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

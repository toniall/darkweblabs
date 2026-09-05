#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.5 — I2P's threat model vs Tor's
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
WS="$HERE/../artifacts/i2p-threat-model/worksheet.md"

echo; echo "Lab 6.5 — I2P's threat model vs Tor's"; echo

ck "the I2P threat-model worksheet ships" \
   "test -f '$WS'"
ck "it re-runs the L x I x E method" \
   "grep -q 'L x I x E' '$WS'"
ck "the NEW floodfill-eclipse row is pre-listed" \
   "grep -qi 'floodfill eclipse' '$WS'"
ck "the leaseSet-harvest row is pre-listed" \
   "grep -qi 'leaseSet gateway harvest' '$WS'"
ck "the testnet the model reasons about is up" \
   "docker ps --format '{{.Names}}' | grep -q '^darkweb-i2p-ff1'"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

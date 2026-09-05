#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.6 — Both networks, side by side
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"

echo; echo "Lab 6.6 — Both networks, side by side"; echo

ck "the Tor base stack is running" \
   "docker ps --format '{{.Names}}' | grep -q '^darkweb-gateway'"
ck "the I2P testnet is running alongside it" \
   "docker ps --format '{{.Names}}' | grep -q '^darkweb-i2p-r1'"
ck "an I2P router has NO clearnet route (the failure IS the pass)" \
   "! docker exec darkweb-i2p-r1 sh -c 'wget -qO- -T5 https://check.torproject.org'"
ck "the Tor workstation still fails closed (Lab 2.7 holds)" \
   "bash '$HERE/2.7.sh'"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

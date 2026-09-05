#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.6 — Threat model vs Tor and I2P
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
WS="$HERE/../artifacts/hyphanet-threat-model/worksheet.md"
echo; echo "Lab 7.6 — Threat model vs Tor and I2P"; echo
ck "the Hyphanet threat-model worksheet ships" \
   "test -f '$WS'"
ck "it re-runs the L x I x E method" \
   "grep -q 'L x I x E' '$WS'"
ck "the NEW compromised-friend row is pre-listed" \
   "grep -qi 'compromised / coerced friend' '$WS'"
ck "the vanished 'no host to seize' row is pre-listed" \
   "grep -qi 'service host located' '$WS'"
ck "the testnet the model reasons about is up (darknet)" \
   "docker exec darkweb-fn-n1 grep -qE '^node.opennet.enabled=false' /data/freenet.ini"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.7 — The complete overlay decision
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
MX="$HERE/../artifacts/overlay-matrix/matrix.md"
echo; echo "Lab 7.7 — The complete overlay decision"; echo
ck "the overlay matrix ships" \
   "test -f '$MX'"
ck "Tor is populated" "grep -q 'Tor' '$MX'"
ck "I2P is populated" "grep -q 'I2P' '$MX'"
ck "Hyphanet is populated (the Chapter 6 stub is filled)" \
   "grep -q 'Hyphanet' '$MX'"
ck "no Hyphanet stub remains" \
   "! grep -qi 'stub: ch07' '$MX'"
ck "it names the decision procedure (threat-model driven)" \
   "grep -qi 'threat model' '$MX'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

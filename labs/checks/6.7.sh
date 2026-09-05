#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.7 — A comparison you can defend
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
MX="$HERE/../artifacts/overlay-matrix/matrix.md"

echo; echo "Lab 6.7 — A comparison you can defend"; echo

ck "the overlay comparison matrix ships" \
   "test -f '$MX'"
ck "Tor is populated in the matrix" \
   "grep -q 'Tor' '$MX'"
ck "I2P is populated in the matrix" \
   "grep -q 'I2P' '$MX'"
ck "a Hyphanet column exists (stubbed at ch06, filled by ch07)" \
   "grep -qi 'Hyphanet' '$MX'"
ck "it names the decision procedure (threat-model driven)" \
   "grep -qi 'threat model' '$MX'"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

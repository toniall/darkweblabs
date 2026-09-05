#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.6 — Cross-network links
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/../artifacts/range-content/seed.py"
MANIFEST="$HERE/../artifacts/range-scorer/manifest.json"
GEN="$(mktemp -d)"; python3 "$SEED" --out "$GEN" >/dev/null 2>&1 || true
echo; echo "Lab 8.6 — Cross-network links"; echo
ck "the ground truth records an I2P cross-link" \
   "grep -q 'i2p' '$MANIFEST'"
ck "the ground truth records a Hyphanet cross-link" \
   "grep -q 'hyphanet' '$MANIFEST'"
ck "the directory links off to an eepsite (.b32.i2p)" \
   "grep -q 'b32.i2p' '$GEN/directory/index.html'"
ck "the directory links off to a Hyphanet freesite (USK@)" \
   "grep -q 'USK@' '$GEN/directory/index.html'"
rm -rf "$GEN"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.5 — Mirrors, clones, and phishing
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/../artifacts/range-content/seed.py"
MANIFEST="$HERE/../artifacts/range-scorer/manifest.json"
GEN="$(mktemp -d)"; python3 "$SEED" --out "$GEN" >/dev/null 2>&1 || true
echo; echo "Lab 8.5 — Mirrors, clones, and phishing"; echo
ck "the generator self-tests mirror-identical + clone-altered" \
   "python3 '$SEED' --selftest"
ck "the mirror is byte-identical to the market" \
   "cmp -s '$GEN/market/index.html' '$GEN/market-mirror/index.html'"
ck "the clone is NOT byte-identical to the market" \
   "! cmp -s '$GEN/market/index.html' '$GEN/market-clone/index.html'"
ck "the ground truth records the clone's altered pgp+btc" \
   "grep -q 'clone' '$MANIFEST' && grep -q 'altered' '$MANIFEST'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

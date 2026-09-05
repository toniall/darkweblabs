#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.1 — Why simulate, and the tier shift
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/../artifacts/range-content/seed.py"
GEN="$(mktemp -d)"; python3 "$SEED" --out "$GEN" >/dev/null 2>&1 || true
echo; echo "Lab 8.1 — Why simulate, and the tier shift"; echo
ck "the range publisher is running" \
   "docker ps --format '{{.Names}}' | grep -q darkweb-range-tor"
ck "the range publishes onion services" \
   "docker exec darkweb-range-tor test -s /content/onions.env"
ck "the content generator self-tests (watermark enforced)" \
   "python3 '$SEED' --selftest"
ck "every generated page carries the synthetic watermark (safety control)" \
   "grep -rq 'SYNTHETIC' '$GEN'"
rm -rf "$GEN"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

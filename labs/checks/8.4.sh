#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.4 — A leak site: persistence and flicker
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/../artifacts/range-content/seed.py"
LABBIN="$HERE/../../lab"
GEN="$(mktemp -d)"; python3 "$SEED" --out "$GEN" >/dev/null 2>&1 || true
echo; echo "Lab 8.4 — A leak site: persistence and flicker"; echo
ck "the leak site is synthetic — no real breach data" \
   "grep -qi 'no real breach' '$GEN/leak/index.html'"
ck "the leak page is watermarked" \
   "grep -q 'SYNTHETIC' '$GEN/leak/index.html'"
ck "a seizure/rebrand flap is available in the CLI" \
   "grep -q 'flap)' '$LABBIN'"
ck "the leak service has its own onion (so it can move)" \
   "docker exec darkweb-range-tor test -d /var/lib/tor/range-leak"
rm -rf "$GEN"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

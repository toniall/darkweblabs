#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.2 — A directory and the seed problem
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/../artifacts/range-content/seed.py"
MANIFEST="$HERE/../artifacts/range-scorer/manifest.json"
GEN="$(mktemp -d)"; python3 "$SEED" --out "$GEN" >/dev/null 2>&1 || true
echo; echo "Lab 8.2 — A directory and the seed problem"; echo
ck "the directory content is served by the range" \
   "docker exec darkweb-range-web test -f /content/directory/index.html"
ck "at least one service is absent from the directory (discovery is incomplete)" \
   "grep -qE 'in_directory.*false' '$MANIFEST'"
ck "the directory lists the market but not the leak site (a subset)" \
   "grep -qi 'market' '$GEN/directory/index.html' && ! grep -qi 'leak' '$GEN/directory/index.html'"
ck "the directory carries a stale/moved entry (real indexes rot)" \
   "grep -qi 'stale\|moved\|gone' '$GEN/directory/index.html'"
rm -rf "$GEN"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.8 — market extraction + vendor graph over the real Agora slice (offline, deterministic)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"; AG="$HERE/../datasets/agora"; DB="$AG/market.db"
echo; echo "Lab 11.8 — market extraction + vendor graph over the real Agora slice"; echo
ck "the market slice ships (scrubbed Agora data)" '[ -f "$DB" ]'
ck "the slice self-tests (pseudonymized vendors, no free-text)" "python3 '$AG/seed.py' --selftest"
ck "the market analyzer self-tests (extraction, vendor graph, calibration)" "python3 '$AG/slice.py' --selftest"
OUT="$(python3 "$AG/slice.py" 2>/dev/null)"
ck "it extracts structured listings and vendors" 'grep -Eq "extracted +[0-9]+ listings" <<< "$OUT"'
ck "it builds a vendor graph with concentration" 'grep -q "vendor concentration" <<< "$OUT"'
ck "it derives real shipping lanes and price tiers to calibrate the synthetic market" 'grep -q "shipping lanes" <<< "$OUT" && grep -q "price tiers" <<< "$OUT"'
ck "no real vendor names leak (all pseudonyms)" "[ \"\$(python3 -c \"import sqlite3; print(sqlite3.connect('$DB').execute(\\\"SELECT COUNT(*) FROM listings WHERE vendor_id NOT LIKE 'vendor-%'\\\").fetchone()[0])\")\" = 0 ]"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

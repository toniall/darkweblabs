#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 14.8 — monitoring over the real ransomwatch change-feed (offline, deterministic)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"; RW="$HERE/../datasets/ransomwatch"; DB="$RW/leaksite.db"
echo; echo "Lab 14.8 — monitoring over the real ransomwatch change-feed"; echo
ck "the leak-site feed ships (built from ransomwatch)" '[ -f "$DB" ]'
ck "the feed self-tests (scrubbed, pseudonymized, chronological)" "python3 '$RW/seed.py' --selftest"
ck "the monitor self-tests (change-feed, severity, taxonomy, correlation)" "python3 '$RW/monitor.py' --selftest"
OUT="$(python3 "$RW/monitor.py" 2>/dev/null)"
ck "it derives a weekly change-feed and flags campaign bursts" 'grep -Eq "severity: bursts +[1-9]" <<< "$OUT"'
ck "it classifies new-victim, repost, and cross-group events" 'grep -q "event taxonomy" <<< "$OUT" && grep -q "cross-group" <<< "$OUT"'
ck "it surfaces a real correlation candidate (one victim, two groups)" 'grep -q "correlation candidate" <<< "$OUT"'
ck "no real victim names leak (all pseudonyms)" "[ \"\$(python3 -c \"import sqlite3; print(sqlite3.connect('$DB').execute(\\\"SELECT COUNT(*) FROM posts WHERE victim_id NOT LIKE 'victim-%'\\\").fetchone()[0])\")\" = 0 ]"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

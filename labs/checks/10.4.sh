#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.4 — Identity without keys: secondary signals
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
DEDUP="$HERE/../artifacts/dedup"
echo; echo "Lab 10.4 — Identity without keys: secondary signals"; echo
ck "signals.py self-test passes" 'python3 "$DEDUP/signals.py" --selftest'
ck "shared-asset detection is implemented" 'grep -q "def shared_assets" "$DEDUP/signals.py"'
ck "payment-swap detection is implemented" 'grep -q "def payment_swapped" "$DEDUP/signals.py"'
ck "the mirror/clone intent rule is implemented" 'grep -q "def intent" "$DEDUP/signals.py"'
ck "key extraction is reused from the Chapter 9 crawler" 'grep -q "from extract import" "$DEDUP/signals.py"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

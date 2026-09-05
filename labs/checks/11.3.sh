#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 11.3 — Anti-crawling: detect, never defeat
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/market-extract"
DEF="$("$LAB" market defenses 2>/dev/null)"
echo; echo "Lab 11.3 — Anti-crawling: detect, never defeat"; echo
ck "defense detector self-tests (captcha/rate-limit/poison/honeypot)" '( cd "$ART" && python3 defenses.py --selftest )'
ck "CAPTCHA routes to queue (for a human), not a solver" 'grep -Eq "captcha.*queue" <<< "$DEF"'
ck "no solver symbol exists in the defenses module" '! grep -Eq "def +solve" "$ART/defenses.py"'
ck "rate limit routes to backoff" 'grep -Eq "rate_limited.*backoff" <<< "$DEF"'
ck "honeypot link detected and skipped" 'grep -q "/trap/" <<< "$DEF"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

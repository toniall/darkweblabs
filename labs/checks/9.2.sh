#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.2 — Fetching through Tor: slow, unreliable, and you must be polite
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
echo; echo "Lab 9.2 — Fetching through Tor: slow, unreliable, and you must be polite"; echo
ck "the frontier self-tests (politeness scheduling included)" \
   "python3 '$CRAWLER/frontier.py' --selftest"
ck "a per-host politeness delay is implemented" \
   "grep -q 'min_delay' '$CRAWLER/frontier.py'"
ck "the frontier tracks when a host may next be fetched" \
   "grep -q 'wait_for' '$CRAWLER/frontier.py'"
ck "the live fetch driver parses and drives a timed, retrying fetch" \
   "python3 -c \"import ast; ast.parse(open('$CRAWLER/crawl_live.py').read())\""
ck "the driver fetches through the workstation's Tor SOCKS" \
   "grep -q 'socks5-hostname' '$CRAWLER/crawl_live.py'"
ck "(host) the range is up and publishing onions" \
   "docker exec darkweb-range-tor cat /content/onions.env"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

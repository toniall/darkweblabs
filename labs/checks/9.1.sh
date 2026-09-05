#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.1 — The frontier: crawling without an index
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
echo; echo "Lab 9.1 — The frontier: crawling without an index"; echo
ck "the frontier self-tests (normalization, seen-set, scope guard, politeness)" \
   "python3 '$CRAWLER/frontier.py' --selftest"
ck "an i2p address classifies by form" \
   "python3 '$CRAWLER/frontier.py' --classify http://identifier.b32.i2p/ | grep -q i2p"
ck "a clearnet address classifies as clearnet (the guard will refuse it)" \
   "python3 '$CRAWLER/frontier.py' --classify https://example.com | grep -q clearnet"
ck "the scope guard is present in the frontier" \
   "grep -q 'in_scope' '$CRAWLER/frontier.py'"
ck "(host) the crawler is mounted in the workstation" \
   "docker exec darkweb-workstation test -f /opt/crawler/crawl.py"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

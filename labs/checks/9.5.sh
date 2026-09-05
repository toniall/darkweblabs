#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.5 — Continuous collection: revisiting a moving target
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
LAB="$HERE/../../lab"
echo; echo "Lab 9.5 — Continuous collection: revisiting a moving target"; echo
ck "the crawler self-tests" \
   "python3 '$CRAWLER/crawl.py' --selftest"
ck "content hashing supports change detection across revisits" \
   "grep -q 'content_hash' '$CRAWLER/extract.py'"
ck "the range can flap a service to a new onion" \
   "grep -q 'flap' '$LAB'"
ck "(host) the range holds live onion state to flap" \
   "docker exec darkweb-range-tor test -d /var/lib/tor"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

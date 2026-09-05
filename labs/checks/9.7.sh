#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.7 — Scoring the crawler and closing the loop
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
SCORER="$HERE/../artifacts/range-scorer/scorer.py"
LAB="$HERE/../../lab"
echo; echo "Lab 9.7 — Scoring the crawler and closing the loop"; echo
ck "the full engine outscores the naive crawl on every axis (checked in-test via the scorer)" \
   "python3 '$CRAWLER/crawl.py' --selftest"
ck "the crawler emits a crawl-output the scorer consumes" \
   "grep -q 'discovered' '$CRAWLER/crawl.py'"
ck "the Chapter 8 scorer still self-tests (the loop's grader)" \
   "python3 '$SCORER' --selftest"
ck "./lab crawl is wired to run and score the crawler" \
   "grep -q 'cmd_crawl' '$LAB'"
ck "(host) the range is up so the full crawl can be scored" \
   "docker exec darkweb-range-tor cat /content/onions.env"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

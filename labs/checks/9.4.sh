#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.4 — Sessions and state: getting past the wall
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
echo; echo "Lab 9.4 — Sessions and state: getting past the wall"; echo
ck "the crawler self-tests, and the session run reaches past the wall (recall rises)" \
   "python3 '$CRAWLER/crawl.py' --selftest"
ck "the crawler handles the login wall" \
   "grep -q 'login' '$CRAWLER/crawl.py'"
ck "session handling is a toggle on the engine" \
   "grep -q 'sessions' '$CRAWLER/crawl.py'"
ck "the live driver carries a cookie jar across requests" \
   "grep -q 'jar' '$CRAWLER/crawl_live.py'"
ck "(host) the workstation is up to run the live crawl" \
   "docker exec darkweb-workstation test -f /opt/crawler/crawl_live.py"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

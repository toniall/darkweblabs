#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.3 — A market and a forum: services have state
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
NGXCONF="$HERE/../../images/range/nginx-range.conf"
echo; echo "Lab 8.3 — A market and a forum: services have state"; echo
ck "the market gates a protected path behind a login" \
   "grep -q 'return 302 /login' '$NGXCONF'"
ck "the protected path keys off a session cookie" \
   "grep -q 'session=' '$NGXCONF'"
ck "a no-session fetch of /listings is redirected, not served (302)" \
   "docker exec darkweb-range-web-clone sh -c 'wget -S -O /dev/null http://range-web:8081/listings 2>&1 | grep -q 302'"
ck "the market serves a login page" \
   "grep -q 'login' '$NGXCONF'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

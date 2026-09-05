#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.5 — Streams
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
echo; echo "Lab 3.5 — Streams"; echo
ck "stream-status is queryable over the control port" "ctl 'GETINFO stream-status' | grep -q 'stream-status'"
ck "circuit-status is queryable over the control port" "ctl 'GETINFO circuit-status' | grep -q 'circuit-status'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

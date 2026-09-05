#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.7 — New identity and circuit hygiene
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
echo; echo "Lab 3.7 — New identity and circuit hygiene"; echo
ck "SIGNAL NEWNYM is accepted" "ctl 'SIGNAL NEWNYM' | grep -q '250 OK'"
ck "MaxCircuitDirtiness is readable" "ctl 'GETCONF MaxCircuitDirtiness' | grep -q 'MaxCircuitDirtiness='"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

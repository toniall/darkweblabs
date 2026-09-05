#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.3 — Guards: your fixed door
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
echo; echo "Lab 3.3 — Guards"; echo
ck "Tor reports at least one entry guard" "ctl 'GETINFO entry-guards' | grep -qE '[\$][0-9A-Fa-f]{40}'"
ck "the guard is recorded in the persistent state file" "docker exec darkweb-gateway grep -q '^Guard' /var/lib/tor/state"
ck "the tor_data volume exists (guard survives reset)" "docker volume ls --format '{{.Name}}' | grep -qx darkweb_tor_data"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

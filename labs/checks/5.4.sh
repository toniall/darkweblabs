#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.4 — Guard discovery and traffic-shaping
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
# capture the guard, request a new identity, capture again — it must not move
G1="$(ctl 'GETINFO entry-guards' 2>/dev/null | grep -oiE '\$[0-9A-F]{40}' | head -1)"
ctl 'SIGNAL NEWNYM' >/dev/null 2>&1 || true
sleep 6
G2="$(ctl 'GETINFO entry-guards' 2>/dev/null | grep -oiE '\$[0-9A-F]{40}' | head -1)"
echo; echo "Lab 5.4 — Guard discovery and traffic-shaping"; echo
ck "the guard is identifiable and unchanged after NEWNYM" \
   "[ -n '$G1' ] && [ '$G1' = '$G2' ]"
ck "the guard is recorded in the persistent state file" \
   "docker exec darkweb-gateway grep -q '^Guard' /var/lib/tor/state"
ck "the tor_data volume exists (the guard survives a reset)" \
   "docker volume ls --format '{{.Name}}' | grep -qx darkweb_tor_data"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

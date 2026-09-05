#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.1 — The adversary model
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
echo; echo "Lab 5.1 — The adversary model"; echo
ck "the gateway uplink is capturable (tcpdump present, eth0 up)" \
   "docker exec darkweb-gateway sh -c 'command -v tcpdump && ip -o addr show eth0'"
ck "the guard — the adversary's prize — is identifiable" \
   "ctl 'GETINFO entry-guards' | grep -qE '[\$][0-9A-Fa-f]{40}'"
ck "the workstation routes through the gateway (the entry path adversaries sit on)" \
   "dex_has darkweb-workstation 'default via 10.152.152.10' ip route"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.1 — The control port as an instrument
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }
echo; echo "Lab 3.1 — The control port as an instrument"; echo
ck "control port authenticates and returns a version" "ctl 'GETINFO version' | grep -q '250-version='"
ck "stem is installed on the workstation" "docker exec darkweb-workstation python3 -c 'import stem'"
ck "stem can connect and authenticate to the gateway" \
   "docker exec darkweb-workstation python3 -c 'import os;from stem.control import Controller;
c=Controller.from_port(address=\"10.152.152.10\",port=9051);c.authenticate(password=os.environ[\"LAB_CONTROL_PW\"]);print(c.get_version());c.close()'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.2 — The consensus: Tor's shared map
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
ctl() { docker exec -e CMD="$1" darkweb-workstation sh -c 'printf "AUTHENTICATE \"%s\"\r\n%s\r\nQUIT\r\n" "$LAB_CONTROL_PW" "$CMD" | nc -w8 10.152.152.10 9051'; }

# Count the relays in the consensus. The program is fed on stdin rather than
# passed with `python3 -c`: a -c string nested inside ck's double quotes has its
# backslashes eaten before python ever sees it, and the result is a SyntaxError,
# not a failed assertion.
relay_count() {
  docker exec -i darkweb-workstation python3 <<'PY'
import os
from stem.control import Controller
c = Controller.from_port(address="10.152.152.10", port=9051)
c.authenticate(password=os.environ["LAB_CONTROL_PW"])
print(len(list(c.get_network_statuses())))
c.close()
PY
}

echo; echo "Lab 3.2 — The consensus"; echo
ck "the gateway holds a current consensus" "ctl 'GETINFO consensus/valid-after' | grep -q 'valid-after='"
ck "it has enough directory info to build circuits" "ctl 'GETINFO status/enough-dir-info' | grep -q 'enough-dir-info=1'"
ck "the consensus lists a non-trivial number of relays" '[ "$(relay_count)" -gt 100 ]'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

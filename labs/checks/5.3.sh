#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.3 — Malicious and colluding relays
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
# one consensus query, three counts: bandwidth-bearing relays, Guard-flagged, Exit-flagged
BW=0; GUARD=0; EXITN=0
read BW GUARD EXITN < <(docker exec darkweb-workstation python3 -c 'import os
from stem.control import Controller
c=Controller.from_port(address="10.152.152.10",port=9051)
c.authenticate(password=os.environ["LAB_CONTROL_PW"])
r=list(c.get_network_statuses())
print(sum(1 for x in r if (x.bandwidth or 0)>0),
      sum(1 for x in r if "Guard" in x.flags),
      sum(1 for x in r if "Exit" in x.flags))
c.close()' 2>/dev/null) || true
BW=${BW:-0}; GUARD=${GUARD:-0}; EXITN=${EXITN:-0}
echo; echo "Lab 5.3 — Malicious and colluding relays"; echo
ck "relays in the consensus carry measured bandwidth weights" "[ '$BW'    -gt 100 ]"
ck "the consensus flags Guard relays"                          "[ '$GUARD' -gt 10 ]"
ck "the consensus flags Exit relays (distinct from Guard)"     "[ '$EXITN' -gt 10 ]"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

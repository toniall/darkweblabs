#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.4 — Building a circuit
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 3.4 — Building a circuit"; echo
ck "at least one BUILT 3-hop general circuit exists" \
   "docker exec darkweb-workstation python3 -c 'import os,sys;from stem.control import Controller;
c=Controller.from_port(address=\"10.152.152.10\",port=9051);c.authenticate(password=os.environ[\"LAB_CONTROL_PW\"]);
ok=any(x.status==\"BUILT\" and x.purpose==\"GENERAL\" and len(x.path)==3 for x in c.get_circuits());c.close();sys.exit(0 if ok else 1)'"
ck "a hand-built circuit also has three hops" \
   "docker exec darkweb-workstation python3 -c 'import os,sys;from stem.control import Controller;
c=Controller.from_port(address=\"10.152.152.10\",port=9051);c.authenticate(password=os.environ[\"LAB_CONTROL_PW\"]);
cid=c.new_circuit(await_build=True);n=len(c.get_circuit(cid).path);c.close();sys.exit(0 if n==3 else 1)'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

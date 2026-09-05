#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 1.4 — Reset discipline
# Two volumes survive a reset (your evidence, and Tor's guard state); one is
# discarded (the workstation scratch). Confirm the volumes exist and are mounted
# where they should be, so `./lab reset` throws away only what it should.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }

vols() { docker volume ls --format '{{.Name}}'; }
mnts() { docker inspect "$1" -f '{{json .Mounts}}'; }

echo
echo "Lab 1.4 — Reset discipline"
echo

ck "evidence volume exists (survives reset)"  "vols | grep -qx darkweb_evidence"
ck "tor_data volume exists (survives reset)"  "vols | grep -qx darkweb_tor_data"
ck "scratch volume exists (discarded by reset)" "vols | grep -qx darkweb_ws_scratch"

echo
ck "evidence is mounted on the workstation"    "mnts darkweb-workstation | grep -q darkweb_evidence"
ck "scratch is mounted on the workstation"     "mnts darkweb-workstation | grep -q darkweb_ws_scratch"
ck "tor guard state is mounted on the gateway" "mnts darkweb-gateway     | grep -q darkweb_tor_data"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]

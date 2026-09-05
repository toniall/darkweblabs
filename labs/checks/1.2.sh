#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 1.2 — Anatomy of the stack
# Three networks now: external (gateway's path out), internal (sealed, the
# torified data path + portal), and deskaccess (the workstation's own desktop
# port). The workstation is a real host on the internal net — not a namespace
# borrower.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }

net() { docker inspect "$1" -f '{{json .NetworkSettings.Networks}}'; }

echo
echo "Lab 1.2 — Anatomy of the stack"
echo

ck "external network exists"   "docker network ls --format '{{.Name}}' | grep -qx darkweb_external"
ck "internal network exists"   "docker network ls --format '{{.Name}}' | grep -qx darkweb_internal"
ck "deskaccess network exists" "docker network ls --format '{{.Name}}' | grep -qx darkweb_deskaccess"

ck "internal network is sealed (internal:true)" \
   "docker network inspect darkweb_internal -f '{{.Internal}}' | grep -qx true"
ck "internal subnet is 10.152.152.0/24" \
   "docker network inspect darkweb_internal -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}' | grep -qx 10.152.152.0/24"

echo
ck "gateway is dual-homed (external + internal)" \
   "net darkweb-gateway | grep -q darkweb_external && net darkweb-gateway | grep -q darkweb_internal"
ck "gateway holds 10.152.152.10 on the internal net" \
   "net darkweb-gateway | grep -q 10.152.152.10"

ck "workstation is on the internal net at 10.152.152.11" \
   "net darkweb-workstation | grep -q 10.152.152.11"
ck "workstation is on the desktop-access net" \
   "net darkweb-workstation | grep -q darkweb_deskaccess"
ck "workstation has NO path to the external net" \
   "! net darkweb-workstation | grep -q darkweb_external"

ck "portal is internal-only at 10.152.152.20" \
   "net darkweb-portal | grep -q 10.152.152.20 && ! net darkweb-portal | grep -q darkweb_external"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]

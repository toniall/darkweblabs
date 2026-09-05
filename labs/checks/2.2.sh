#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.2 — Watch what actually leaves
# DNS is redirected into Tor's DNSPort at the gateway; names resolve without any
# clear port-53 traffic leaving the uplink.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
echo; echo "Lab 2.2 — Watch what actually leaves"; echo
ck "gateway redirects workstation DNS into Tor's DNSPort" \
   "dex_has darkweb-gateway 'REDIRECT --to-ports 5353' iptables -t nat -S PREROUTING"
ck "Tor's DNSPort is listening on the gateway (udp/5353)" \
   "docker exec darkweb-gateway sh -c 'ss -lun 2>/dev/null || netstat -lun' | grep -q ':5353'"
# Either family proves the point: the name resolved, and it resolved through
# Tor's DNSPort. Tor answers AAAA for plenty of hosts, so grading on a dotted
# quad fails on a stack that is working correctly.
ck "a name resolves from the workstation (through Tor)" \
   "dex_has darkweb-workstation '([0-9]+\\.){3}[0-9]+|:' getent ahosts example.com"
ck "the gateway's DNSPort is not exposed on the external side" \
   "! docker exec darkweb-gateway sh -c 'ss -lun 2>/dev/null || netstat -lun' | grep -q '172\\..*:5353'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

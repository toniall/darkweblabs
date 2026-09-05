#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 1.3 — The gateway route
# The workstation is a separate host whose ONLY route off the machine is the
# gateway. The gateway redirects its TCP and DNS into Tor and rejects anything
# it cannot carry. This replaces the old shared-namespace model: isolation is
# now enforced by routing + firewall, not by borrowing one network stack.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"

echo
echo "Lab 1.3 — The gateway route"
echo

# Separate hosts now — the opposite of the old namespace binding.
ck "workstation and gateway are DIFFERENT network namespaces" \
   "[ \"\$(docker exec darkweb-workstation readlink /proc/self/ns/net)\" != \
      \"\$(docker exec darkweb-gateway     readlink /proc/self/ns/net)\" ]"

ck "workstation's default route is the gateway (10.152.152.10)" \
   "dex_has darkweb-workstation '^default via 10.152.152.10' ip route"
ck "workstation resolves through the gateway" \
   "docker exec darkweb-workstation grep -q '10.152.152.10' /etc/resolv.conf"

echo
# The gateway does the torifying.
ck "gateway redirects workstation TCP into Tor's TransPort" \
   "dex_has darkweb-gateway 'REDIRECT --to-ports 9040' iptables -t nat -S PREROUTING"
ck "gateway redirects DNS into Tor" \
   "dex_has darkweb-gateway 'REDIRECT --to-ports 5353' iptables -t nat -S PREROUTING"
ck "gateway lets SOCKS traffic reach Tor (not the TransPort)" \
   "dex_has darkweb-gateway 'd 10.152.152.10.* -j RETURN' iptables -t nat -S PREROUTING"
ck "gateway fails closed (FORWARD rejects the rest)" \
   "dex_has darkweb-gateway 'REJECT' iptables -S FORWARD"

echo
# Prove it end to end from the workstation.
ck "SOCKS on the gateway carries the workstation over Tor" \
   "docker exec darkweb-workstation curl -s --max-time 30 \
      --socks5-hostname 10.152.152.10:9050 https://check.torproject.org/api/ip \
      | grep -q '\"IsTor\":true'"
ck "the control port is reachable from the workstation" \
   "docker exec darkweb-workstation sh -c 'nc -w3 10.152.152.10 9051 </dev/null'"
ck "a full compromise still can't leak: raw ICMP is rejected" \
   "! docker exec darkweb-workstation ping -c1 -W3 1.1.1.1"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]

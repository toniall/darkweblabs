#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.4 — Behavioural vs structural: proxychains vs the gateway
# proxychains works but is opt-in; the gateway torifies a bare, un-wrapped tool
# anyway via a netfilter redirect, and exempts traffic to itself.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
echo; echo "Lab 2.4 — proxychains vs the gateway"; echo
ck "proxychains is installed" \
   "docker exec darkweb-workstation sh -c 'command -v proxychains4 || command -v proxychains'"
ck "proxychains points at the gateway's SOCKS port" \
   "docker exec darkweb-workstation sh -c 'grep -rq \"10.152.152.10\" /etc/proxychains*.conf 2>/dev/null || grep -rq \"10.152.152.10 9050\" /etc 2>/dev/null'"
ck "a bare curl (no proxychains, no flag) is torified anyway" \
   "docker exec darkweb-workstation curl -s --max-time 30 \
      https://check.torproject.org/api/ip | grep -q '\"IsTor\":true'"
ck "the gateway redirects workstation TCP into Tor's TransPort (9040)" \
   "dex_has darkweb-gateway 'REDIRECT --to-ports 9040' iptables -t nat -S PREROUTING"
ck "traffic to the gateway itself is exempted (SOCKS/control stay reachable)" \
   "dex_has darkweb-gateway 'd 10.152.152.10.* -j RETURN' iptables -t nat -S PREROUTING"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

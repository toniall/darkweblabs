#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 1.1 — First light
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }

echo
echo "Lab 1.1 — First light"
echo

ck "gateway is healthy" \
   "[ \"\$(docker inspect -f '{{.State.Health.Status}}' darkweb-gateway)\" = healthy ]"
ck "workstation is healthy" \
   "[ \"\$(docker inspect -f '{{.State.Health.Status}}' darkweb-workstation)\" = healthy ]"
ck "portal is healthy" \
   "[ \"\$(docker inspect -f '{{.State.Health.Status}}' darkweb-portal)\" = healthy ]"
ck "desktop is bound to localhost only" \
   "docker compose ps --format '{{.Ports}}' | grep -q '127.0.0.1:6901'"
ck "preflight report exists" \
   "[ -s \"\${LAB_EVIDENCE:-\$HOME/evidence}/preflight.json\" ]"
ck "workstation exits through Tor" \
   "docker exec darkweb-workstation curl -s --max-time 30 \
      https://check.torproject.org/api/ip | grep -q '\"IsTor\":true'"
ck "ICMP is refused, not forwarded" \
   "! docker exec darkweb-workstation ping -c1 -W3 8.8.8.8"

echo
ck "gateway redirects workstation TCP into Tor" \
   "docker exec darkweb-gateway iptables -t nat -S PREROUTING \
      | grep -q 'REDIRECT --to-ports 9040'"
ck "clipboard bridge running" \
   "docker exec darkweb-workstation pgrep -f vncconfig"

echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]

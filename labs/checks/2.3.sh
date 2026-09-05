#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.3 — The browser is a fingerprint
# Both browsers are installed and both exit through Tor (via the gateway), so
# any difference between them is above the network — the fingerprint surface.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 2.3 — The browser is a fingerprint"; echo
ck "Tor Browser is installed" \
   "docker exec darkweb-workstation test -x /opt/tor-browser/Browser/start-tor-browser"
ck "Firefox is installed" \
   "docker exec darkweb-workstation sh -c 'command -v firefox || command -v firefox-esr'"
ck "Tor Browser is pointed at the gateway's SOCKS port" \
   "docker exec darkweb-workstation grep -rq '10.152.152.10' /usr/local/bin/tor-browser"
ck "both browsers exit through Tor (network already closed in 2.1)" \
   "docker exec darkweb-workstation curl -s --max-time 30 \
      https://check.torproject.org/api/ip | grep -q '\"IsTor\":true'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

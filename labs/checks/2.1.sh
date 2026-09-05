#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.1 — The four leak surfaces
# The network path is closed structurally: a plain curl, with no proxy asked
# for, is torified anyway because the gateway carries nothing else.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 2.1 — The four leak surfaces"; echo
ck "a plain (un-proxied) curl from the workstation exits through Tor" \
   "docker exec darkweb-workstation curl -s --max-time 30 \
      https://check.torproject.org/api/ip | grep -q '\"IsTor\":true'"
ck "it is NOT reporting a direct/clear IP" \
   "! docker exec darkweb-workstation curl -s --max-time 30 \
      https://check.torproject.org/api/ip | grep -q '\"IsTor\":false'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

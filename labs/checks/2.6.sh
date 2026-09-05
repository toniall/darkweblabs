#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.6 — Keyed onions and their friction
# The Add Onion Key launcher registers a client-auth key with the gateway's Tor
# (the daemon that fetches the descriptor), since the browser's prompt can't
# fire on the split.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 2.6 — Keyed onions and their friction"; echo
ck "the Add Onion Key helper is installed" \
   "docker exec darkweb-workstation test -x /usr/local/bin/add-onion-key"
ck "a desktop launcher for it is present" \
   "docker exec darkweb-workstation sh -c 'ls /usr/share/darkweb/desktop/add-onion-key.desktop'"
ck "it targets the gateway's control port" \
   "docker exec darkweb-workstation grep -q '9051' /usr/local/bin/add-onion-key"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

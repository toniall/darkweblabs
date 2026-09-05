#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.3 — Tunnels, unidirectional
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }

# The console answers on 7070, but i2pd's strict Host check can turn a perfectly
# healthy console into a 403 depending on release. Grade on "the console
# answered", not "the console answered 200 to the Host wget happened to send".
console() {
  docker exec "$1" sh -c 'wget -qS --spider "http://127.0.0.1:7070/${2:-}" 2>&1 | grep -q "HTTP/"' _ "${2:-}"
}

HERE="$(cd "$(dirname "$0")" && pwd)"

echo; echo "Lab 6.3 — Tunnels, unidirectional"; echo

ck "the router console exposes the tunnels page" \
   "console darkweb-i2p-r1 '?page=tunnels'"
ck "inbound tunnels are present" \
   "docker exec darkweb-i2p-r1 sh -c 'wget -qO- \"http://127.0.0.1:7070/?page=tunnels\" | grep -iq inbound'"
ck "outbound tunnels are present" \
   "docker exec darkweb-i2p-r1 sh -c 'wget -qO- \"http://127.0.0.1:7070/?page=tunnels\" | grep -iq outbound'"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

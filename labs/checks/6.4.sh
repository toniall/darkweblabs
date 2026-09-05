#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.4 — Eepsites: access and host
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
ECL="$HERE/../artifacts/i2p-netdb/eclipse.py"

# The console answers on 7070, but i2pd's strict Host check can turn a perfectly
# healthy console into a 403 depending on release. Grade on "the console
# answered", not "the console answered 200 to the Host wget happened to send".
console() {
  docker exec "$1" sh -c 'wget -qS --spider "http://127.0.0.1:7070/${2:-}" 2>&1 | grep -q "HTTP/"' _ "${2:-}"
}


echo; echo "Lab 6.4 — Eepsites: access and host"; echo

ck "the HTTP proxy is configured for fetching eepsites (port 4444)" \
   "docker exec darkweb-i2p-r1 grep -qE '^port = 4444' /home/i2pd/data/i2pd.conf"
ck "a client router can reach its own console" \
   "console darkweb-i2p-r2"
ck "b32 addressing: the analyzer resolves a destination to a routing key" \
   "python3 '$ECL' --target labcheck --floodfills /nonexistent"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

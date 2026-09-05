#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.1 — An I2P router in the lab
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"

# The console answers on 7070, but i2pd's strict Host check can turn a perfectly
# healthy console into a 403 depending on release. Grade on "the console
# answered", not "the console answered 200 to the Host wget happened to send".
console() {
  docker exec "$1" sh -c 'wget -qS --spider "http://127.0.0.1:7070/${2:-}" 2>&1 | grep -q "HTTP/"' _ "${2:-}"
}

# A closed testnet converges in minutes, not instantly. Give it a bounded wait
# rather than grading the NetDB the moment the containers report up.
NETDB_WAIT="${LAB_I2P_WAIT:-240}"
wait_netdb() {
  n=0
  while [ "$n" -lt "$NETDB_WAIT" ]; do
    # >= 1 real peer file. `-type f -name '*.dat'` rather than a routerInfo-*
    # glob: peers land as netDb/rX/routerInfo-<hash>.dat, and this is the same
    # definition the compose healthcheck and ./lab i2p netdb use.
    [ "$(docker exec darkweb-i2p-r1 sh -c \
          'find /home/i2pd/data/netDb -type f -name "*.dat" 2>/dev/null | wc -l' \
          2>/dev/null || echo 0)" -ge 1 ] && return 0
    sleep 10; n=$((n+10))
  done
  return 1
}

echo; echo "Lab 6.1 — An I2P router in the lab"; echo

ck "testnet routers are running" \
   "docker ps --format '{{.Names}}' | grep -q '^darkweb-i2p-r1'"
ck "routers pin the custom netid (42)" \
   "docker exec darkweb-i2p-r1 grep -qE '^netid = 42' /home/i2pd/data/i2pd.conf"
ck "the i2p network is internal — no route out" \
   "docker network inspect darkweb_i2pnet -f '{{.Internal}}' | grep -qx true"
echo "  ...  waiting up to ${NETDB_WAIT}s for the testnet to converge"
ck "the NetDB has learned peers (testnet converging)" "wait_netdb"
ck "a router console is up — it has joined the network" \
   "console darkweb-i2p-r1"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

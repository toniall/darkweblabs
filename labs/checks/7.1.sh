#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.1 — A node in a friend mesh
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
echo; echo "Lab 7.1 — A node in a friend mesh"; echo
ck "the Hyphanet nodes are running" \
   "docker ps --format '{{.Names}}' | grep -q '^darkweb-fn-n1'"
ck "opennet is disabled — the node is darknet-only" \
   "docker exec darkweb-fn-n1 grep -qE '^node.opennet.enabled=false' /data/freenet.ini"
ck "the hyphanet network is internal — no route out" \
   "docker network inspect darkweb_fnnet -f '{{.Internal}}' | grep -qx true"
ck "the node's FProxy web interface is reachable" \
   "docker exec darkweb-fn-n1 wget -qO- http://127.0.0.1:8888/"
ck "the node has a datastore configured (it contributes storage)" \
   "docker exec darkweb-fn-n1 grep -qE '^node.storeSize=' /data/freenet.ini"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

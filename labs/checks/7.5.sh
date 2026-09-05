#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.5 — Deniability and the datastore
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
echo; echo "Lab 7.5 — Deniability and the datastore"; echo
ck "the node has a datastore of a configured size" \
   "docker exec darkweb-fn-n1 grep -qE '^node.storeSize=' /data/freenet.ini"
ck "the store is the encrypted salt-hash type (operator can't enumerate plaintext)" \
   "docker exec darkweb-fn-n1 grep -qE '^node.storeType=salt-hash' /data/freenet.ini"
ck "the node is up" \
   "docker exec darkweb-fn-n1 wget -qO- http://127.0.0.1:8888/"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

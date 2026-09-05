#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.2 — Insert, retrieve, and outlive the publisher
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
RT="$HERE/../artifacts/hyphanet-routing/routing.py"
echo; echo "Lab 7.2 — Insert, retrieve, and outlive the publisher"; echo
ck "content-hash-key logic self-tests (address = hash; tampering detected)" \
   "python3 '$RT' --selftest"
ck "FCP is enabled for insert/retrieve" \
   "docker exec darkweb-fn-n1 grep -qE '^fcp.enabled=true' /data/freenet.ini"
ck "a node is up to serve retrievals" \
   "docker exec darkweb-fn-n3 wget -qO- http://127.0.0.1:8888/"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

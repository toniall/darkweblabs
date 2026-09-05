#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.3 — Mutable content: SSK, USK, freesites
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
echo; echo "Lab 7.3 — Mutable content: SSK, USK, freesites"; echo
ck "FCP is enabled (key generation + site insert run over it)" \
   "docker exec darkweb-fn-n1 grep -qE '^fcp.enabled=true' /data/freenet.ini"
ck "FProxy is up to browse the freesite" \
   "docker exec darkweb-fn-n1 grep -qE '^fproxy.enabled=true' /data/freenet.ini"
ck "another node is up to fetch the site by version" \
   "docker exec darkweb-fn-n3 wget -qO- http://127.0.0.1:8888/"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

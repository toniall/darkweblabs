#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 7.4 — Opennet vs darknet
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
RT="$HERE/../artifacts/hyphanet-routing/routing.py"
echo; echo "Lab 7.4 — Opennet vs darknet"; echo
ck "opennet is disabled (darknet only)" \
   "docker exec darkweb-fn-n1 grep -qE '^node.opennet.enabled=false' /data/freenet.ini"
ck "the node is pinned to the friends-only threat level" \
   "docker exec darkweb-fn-n1 grep -qE '^security-levels.networkThreatLevel=HIGH' /data/freenet.ini"
ck "small-world key routing self-tests (greedy routing converges on the graph)" \
   "python3 '$RT' --selftest"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

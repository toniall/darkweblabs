#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 6.2 — The NetDB and floodfill
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
ECL="$HERE/../artifacts/i2p-netdb/eclipse.py"

echo; echo "Lab 6.2 — The NetDB and floodfill"; echo

# One definition of "has peers" across the healthcheck, Lab 6.1 and this check.
ck "the NetDB holds routerInfos" \
   "[ \"\$(docker exec darkweb-i2p-ff1 sh -c 'find /home/i2pd/data/netDb -type f -name \"*.dat\" 2>/dev/null | wc -l' 2>/dev/null || echo 0)\" -ge 1 ]"
ck "floodfills are flagged floodfill = true" \
   "docker exec darkweb-i2p-ff1 grep -qE '^floodfill = true' /home/i2pd/data/i2pd.conf"
ck "plain routers are NOT floodfills" \
   "docker exec darkweb-i2p-r1 grep -qE '^floodfill = false' /home/i2pd/data/i2pd.conf"
ck "eclipse analyzer self-tests (Kademlia XOR distance + daily rotation)" \
   "python3 '$ECL' --selftest"

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

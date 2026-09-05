#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.6 — How onion services get found (verify the leaky artifact leaks; the
# full onion round-trip is the lab, this check tests the leak directly)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
ART="$HERE/../artifacts/leaky/server.py"
P=8992
echo; echo "Lab 4.6 — How onion services get found"; echo
if [ -f "$ART" ]; then
  docker cp "$ART" darkweb-workstation:/tmp/leaky.py >/dev/null 2>&1
  docker exec -d darkweb-workstation sh -c "LEAKY_PORT=$P python3 /tmp/leaky.py" >/dev/null 2>&1
  sleep 1
  ck "the leaky service leaks a backend address in its headers" \
    "dex_hasi darkweb-workstation 'X-Served-By' curl -sI http://127.0.0.1:$P/"
  ck "its /server-status page leaks the host's real address" \
    "dex_has darkweb-workstation 'Local address' curl -s http://127.0.0.1:$P/server-status"
  docker exec darkweb-workstation pkill -f /tmp/leaky.py >/dev/null 2>&1 || true
else
  echo "  FAIL  leaky artifact not found at $ART"; fail=1
fi
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

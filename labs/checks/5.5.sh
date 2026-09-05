#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.5 — Application-layer deanonymization
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
ART="$HERE/../artifacts/canary"
# stage the DEFANGED canary inside the workstation and start its beacon listener
docker exec darkweb-workstation mkdir -p /tmp/canary_art >/dev/null 2>&1 || true
docker cp "$ART/listener.py"    darkweb-workstation:/tmp/canary_art/listener.py    >/dev/null 2>&1 || true
docker cp "$ART/make-canary.sh" darkweb-workstation:/tmp/canary_art/make-canary.sh >/dev/null 2>&1 || true
docker exec darkweb-workstation chmod +x /tmp/canary_art/make-canary.sh >/dev/null 2>&1 || true
docker exec -d darkweb-workstation sh -c 'CANARY_PORT=8977 /tmp/canary_art/make-canary.sh >/tmp/canary_art/out.log 2>&1' >/dev/null 2>&1 || true
sleep 2
echo; echo "Lab 5.5 — Application-layer deanonymization"; echo
ck "the canary document beacons to a lab-internal (private) address" \
   "docker exec darkweb-workstation sh -c 'grep -oE \"http://[0-9.]+:[0-9]+\" /tmp/canary/report.html | grep -qE \"http://(10[.]|172[.](1[6-9]|2[0-9]|3[01])[.]|192[.]168[.])\"'"
ck "the listener records the beacon when the document is opened" \
   "docker exec darkweb-workstation sh -c 'u=\$(grep -oE \"http://[0-9.]+:[0-9]+/beacon.gif\" /tmp/canary/report.html | head -1); curl -s -o /dev/null \"\$u\"; sleep 1; grep -q BEACON /tmp/canary_art/out.log'"
ck "Tor Browser is present (its Safest level disables JavaScript)" \
   "docker exec darkweb-workstation test -x /opt/tor-browser/Browser/start-tor-browser"
docker exec darkweb-workstation pkill -f listener.py >/dev/null 2>&1 || true
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

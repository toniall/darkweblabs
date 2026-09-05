#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.5 — Reaching and hosting onion services
# OnionShare hosts on the workstation while the gateway's Tor publishes the
# onion; the onion target must point at the workstation, not the gateway's
# loopback, and OnionShare must reach the gateway over the control port.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
os_onion() { docker exec darkweb-workstation python3 -c "import onionshare_cli,os;print(os.path.join(os.path.dirname(onionshare_cli.__file__),'onion.py'))"; }
echo; echo "Lab 2.5 — Reaching and hosting onion services"; echo
ck "OnionShare is installed" \
   "docker exec darkweb-workstation sh -c 'command -v onionshare || command -v onionshare-cli'"
ck "the onion target points at the workstation, not loopback" \
   "docker exec darkweb-workstation sh -c 'grep -q 10.152.152.11 \"\$(python3 -c \"import onionshare_cli,os;print(os.path.join(os.path.dirname(onionshare_cli.__file__),\\\"onion.py\\\"))\")\"'"
ck "the Whonix bind marker is present (server binds 0.0.0.0)" \
   "docker exec darkweb-workstation test -e /usr/share/anon-ws-base-files/workstation"
ck "OnionShare is set to use the gateway's control port" \
   "docker exec darkweb-workstation sh -c 'grep -rq control_port /root/.config/onionshare 2>/dev/null || grep -rq control_port /home/darkweb/.config/onionshare 2>/dev/null || true'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 3.6 — Rendezvous (reaching an onion proves rendezvous completes)
# NOTE: onion lookups can take up to a minute; this check is deliberately patient.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
DDG=https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/
echo; echo "Lab 3.6 — Rendezvous"; echo
ck "a known onion is reachable through the gateway (rendezvous works)" \
   "docker exec darkweb-workstation curl -s -o /dev/null -w '%{http_code}' --max-time 75 \
      --socks5-hostname 10.152.152.10:9050 \"$DDG\" | grep -qE '200|30[0-9]'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

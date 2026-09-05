#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.1 — Anatomy of a v3 address (pure decode; no daemon needed)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 4.1 — Anatomy of a v3 address"; echo
ck "a v3 address decodes to 35 bytes, version 3, valid checksum" \
  "docker exec darkweb-workstation python3 -c 'import base64,hashlib,sys
a=\"duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad\"
r=base64.b32decode(a.upper()); pk,cs,ver=r[:32],r[32:34],r[34]
w=hashlib.sha3_256(b\".onion checksum\"+pk+bytes([ver])).digest()[:2]
sys.exit(0 if (len(r)==35 and ver==3 and cs==w) else 1)'"
ck "a corrupted address fails its checksum (proves the check is real)" \
  "! docker exec darkweb-workstation python3 -c 'import base64,hashlib,sys
a=\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaad\"
r=base64.b32decode((a+\"a\").upper()); pk,cs,ver=r[:32],r[32:34],r[34]
w=hashlib.sha3_256(b\".onion checksum\"+pk+bytes([ver])).digest()[:2]
sys.exit(0 if cs==w else 1)'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

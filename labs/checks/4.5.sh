#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.5 — Vanity addresses (derivation proves a vanity address is legitimate;
# mkp224o is the grinder, built in-lab and not required for this check)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 4.5 — Vanity addresses"; echo
ck "a v3 address derives correctly from an ed25519 key and round-trips" \
  "docker exec darkweb-workstation python3 -c 'import base64,hashlib,sys
from nacl.signing import SigningKey
vk=bytes(SigningKey.generate().verify_key)
cs=hashlib.sha3_256(b\".onion checksum\"+vk+b\"\x03\").digest()[:2]
addr=base64.b32encode(vk+cs+b\"\x03\").decode().lower()
r=base64.b32decode(addr.upper())
sys.exit(0 if (len(addr)==56 and r[:32]==vk and r[34]==3) else 1)'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

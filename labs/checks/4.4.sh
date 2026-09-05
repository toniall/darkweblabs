#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.4 — Client authorization, properly
# NOTE: client_auth_v3 takes a base32 string, not a list. Passing [pub] makes
# stem stringify the list, so tor receives ClientAuthV3=['ABC...'] and answers
# "Bad arguments to ADD_ONION". Stem adds Flags=V3Auth itself.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
echo; echo "Lab 4.4 — Client authorization"; echo
ck "PyNaCl is available for x25519 client keypairs" \
  "docker exec darkweb-workstation python3 -c 'import nacl.public'"
ck "an onion published with ClientAuthV3 succeeds" \
  "docker exec darkweb-workstation python3 -c 'import os,base64,sys
from nacl.public import PrivateKey
from stem.control import Controller
sk=PrivateKey.generate()
pub=base64.b32encode(bytes(sk.public_key)).decode().rstrip(\"=\")
c=Controller.from_port(address=\"10.152.152.10\",port=9051)
c.authenticate(password=os.environ[\"LAB_CONTROL_PW\"])
r=c.create_ephemeral_hidden_service({80:\"10.152.152.11:8080\"},key_type=\"NEW\",key_content=\"ED25519-V3\",client_auth_v3=pub)
ok=len(r.service_id)==56
c.remove_ephemeral_hidden_service(r.service_id); c.close()
sys.exit(0 if ok else 1)'"
ck "the base32 client key converts to base64 and round-trips" \
  "docker exec darkweb-workstation python3 -c 'import base64,sys
raw=bytes(range(32)); b32=base64.b32encode(raw).decode().rstrip(\"=\")
k=b32.upper()+\"=\"*((8-len(b32)%8)%8)
sys.exit(0 if base64.b64decode(base64.b64encode(base64.b32decode(k)))==raw else 1)'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

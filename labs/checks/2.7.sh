#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 2.7 — When the gateway says no
# Fail-closed: the FORWARD policy is DROP with an explicit reject, and there is
# no rule forwarding new un-torified traffic out. A raw probe to the clear
# internet is rejected, not leaked.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
echo; echo "Lab 2.7 — When the gateway says no"; echo
ck "the gateway's FORWARD policy is DROP" \
   "dex_has darkweb-gateway '^-P FORWARD DROP' iptables -S FORWARD"
ck "the gateway explicitly REJECTs un-carried traffic" \
   "dex_has darkweb-gateway 'REJECT' iptables -S FORWARD"
ck "established connections are allowed back" \
   "dex_has darkweb-gateway 'ESTABLISHED' iptables -S FORWARD"
ck "a raw-socket probe (ICMP) to the clear internet gets no reply" \
   "! docker exec darkweb-workstation ping -c1 -W3 1.1.1.1"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.6 — Mirror vs clone: redundancy vs impersonation
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
RUN="$("$LAB" dedup run 2>/dev/null)"
echo; echo "Lab 10.6 — Mirror vs clone: redundancy vs impersonation"; echo
ck "the clustering labels same-operator mirrors" 'grep -q "\"role\": \"mirror\"" <<< "$RUN"'
ck "the clustering labels impersonating clones" 'grep -q "\"role\": \"clone\"" <<< "$RUN"'
ck "a swapped payment identity is flagged as impersonation" 'grep -q "payment_swap" <<< "$RUN"'
ck "the keyless clone is caught without any key comparison" 'grep -q "keyless_copy" <<< "$RUN"'
ck "same-operator mirrors are recognised by shared payment" 'grep -q "shared_payment" <<< "$RUN"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

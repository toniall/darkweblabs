#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.5 — The negotiation channel
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/leak-extract"
N="$("$LAB" leak negotiate 2>/dev/null)"
echo; echo "Lab 12.5 — The negotiation channel"; echo
ck "negotiation.py self-tests (arc + tactics)" '( cd "$ART" && python3 negotiation.py --selftest )'
ck "Northwind arc: demand 100 settles at 40" 'grep -Eq "Northwind.*100.*settle 40" <<< "$N"'
ck "Meridian outcome published, threatens to notify a regulator" 'grep -Eq "Meridian.*published.*threat_notify" <<< "$N"'
ck "Apex outcome ongoing, threatens to sell" 'grep -Eq "Apex.*ongoing.*threat_sell" <<< "$N"'
ck "deletion promise recovered on a settled negotiation" 'grep -Eq "Northwind.*deletion_promise" <<< "$N"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

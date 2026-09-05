#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.6 — The bluff is in the gap
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
ART="$HERE/../artifacts/leak-extract"
C="$("$LAB" leak correlate 2>/dev/null)"
echo; echo "Lab 12.6 — The bluff is in the gap"; echo
ck "correlate.py self-tests (public vs private)" '( cd "$ART" && python3 correlate.py --selftest )'
ck "Northwind: deadline, volume, and deletion bluffs" 'grep -Eq "Northwind.*deadline_bluff, volume_bluff, deletion_bluff" <<< "$C"'
ck "Meridian: no bluff — it followed through" 'grep -Eq "Meridian.*no bluff" <<< "$C"'
ck "Coastal: unverifiable deletion bluff" 'grep -Eq "Coastal.*deletion_bluff" <<< "$C"'
ck "Apex: sold-as-leverage bluff" 'grep -Eq "Apex.*sold_bluff" <<< "$C"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

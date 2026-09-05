#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 15.6 — What would change this
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
REP="$($LAB capstone report 2>&1)"
echo; echo "Lab 15.6 — What would change this"; echo
ck "the report carries a what-would-change-this section" 'grep -E "WHAT WOULD CHANGE THIS:" <<< "$REP"'
ck "every finding is paired with a falsifier" 'test $(grep -Ec "^  - [a-z_]+:" <<< "$REP") -ge 8'
ck "the do-not-attribute negative finding names Mimic as a separate operator" 'grep -E "Mimic displays Alpha.s key but signs its own" <<< "$REP"'
ck "the attribution boundary stops at the operator, not a person" 'grep -E "does NOT identify a natural person" <<< "$REP"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

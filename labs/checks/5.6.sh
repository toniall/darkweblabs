#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.6 — Hardening pass: hunt your own leaks
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
echo; echo "Lab 5.6 — Hardening pass: hunt your own leaks"; echo
ck "DNS is still torified (Lab 2.2 holds)"          "bash '$HERE/2.2.sh'"
ck "the gateway still fails closed (Lab 2.7 holds)" "bash '$HERE/2.7.sh'"
ck "the guard is still persisted (Lab 3.3 holds)"   "bash '$HERE/3.3.sh'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

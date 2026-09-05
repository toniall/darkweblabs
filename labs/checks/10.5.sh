#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 10.5 — Clustering: one operator, many addresses
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
DEDUP="$HERE/../artifacts/dedup"
RUN="$("$LAB" dedup run 2>/dev/null)"
echo; echo "Lab 10.5 — Clustering: one operator, many addresses"; echo
ck "cluster.py self-test passes (naive vs full, loop closed)" 'python3 "$DEDUP/cluster.py" --selftest'
ck "union-find is implemented" 'grep -q "_UF" "$DEDUP/cluster.py"'
ck "the full engine produces four clusters" '[ "$(grep -c "\"members\"" <<< "$RUN")" -eq 4 ]'
ck "the market and its look-alikes collapse into one cluster" 'grep -q "market-clone-keyless" <<< "$RUN"'
ck "the decoy market is NOT merged (own cluster)" 'grep -q "\"canonical\": \"other-market.html\"" <<< "$RUN"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

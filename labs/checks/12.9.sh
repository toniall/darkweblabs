#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.9 — leak-site channel over the real ransomwatch feed (offline, deterministic)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"; RW="$HERE/../datasets/ransomwatch"; DB="$RW/leaksite.db"
echo; echo "Lab 12.9 — leak-site channel over the real ransomwatch feed"; echo
ck "the leak-site feed ships" '[ -f "$DB" ]'
ck "the leak-site analyzer self-tests (extraction, lifecycle, reposts, cross-group)" "python3 '$RW/sites.py' --selftest"
OUT="$(python3 "$RW/sites.py" 2>/dev/null)"
ck "it extracts victims per group and a group lifecycle span" 'grep -q "longest running" <<< "$OUT"'
ck "it finds victims reposted more than once" 'grep -Eq "reposts +[1-9]" <<< "$OUT"'
ck "it finds cross-group victims (re-extortion)" 'grep -Eq "cross-group +[1-9]" <<< "$OUT"'
ck "it shows a real re-extortion example (a victim on multiple groups)" 'grep -q "example" <<< "$OUT"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

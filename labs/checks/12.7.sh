#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.7 — Scoring, operator tells, and the hand-off
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
SCO="$HERE/../artifacts/leak-scorer"
SFULL="$("$LAB" leak score 2>/dev/null)"
SNAIVE="$("$LAB" leak score --naive 2>/dev/null)"
echo; echo "Lab 12.7 — Scoring, operator tells, and the hand-off"; echo
ck "leak scorer self-tests" '( cd "$SCO" && python3 scorer.py --selftest )'
ck "full: victim field recall 48/48" 'grep -Eq "victim field recall +48 / 48" <<< "$SFULL"'
ck "full: lifecycle recall 5/5" 'grep -Eq "lifecycle recall +5 / 5" <<< "$SFULL"'
ck "full: repost recall 2/2" 'grep -Eq "repost recall +2 / 2" <<< "$SFULL"'
ck "full: tactic recall 12/12" 'grep -Eq "tactic recall +12 / 12" <<< "$SFULL"'
ck "full: bluff recall 5/5" 'grep -Eq "bluff recall +5 / 5" <<< "$SFULL"'
ck "naive: field recall drops to 42/48" 'grep -Eq "victim field recall +42 / 48" <<< "$SNAIVE"'
ck "naive: lifecycle recall 0/5" 'grep -Eq "lifecycle recall +0 / 5" <<< "$SNAIVE"'
ck "naive: tactic recall 0/12" 'grep -Eq "tactic recall +0 / 12" <<< "$SNAIVE"'
ck "naive: bluff recall 0/5" 'grep -Eq "bluff recall +0 / 5" <<< "$SNAIVE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

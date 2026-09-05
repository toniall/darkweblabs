#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.8 — RansomChat: the negotiation DB and transcript analysis
# The live chat needs Docker + Ollama and is ungraded; this check covers the
# DETERMINISTIC parts: the committed DB built from the Casualtek corpus, and the
# analyzer that reads a saved transcript (offer staircase, tactics, bluffs).
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
RC="$HERE/../artifacts/ransomchat"
DB="$RC/negotiations.db"

echo; echo "Lab 12.8 — RansomChat: the negotiation DB and transcript analysis"; echo

ck "the negotiations DB ships (built from the Casualtek corpus)" '[ -f "$DB" ]'
ck "the DB self-tests: 3 groups, transcripts and messages present, no PII leaks" \
   "python3 '$RC/seed.py' --selftest"
ck "the DB holds Akira, Conti and REvil" \
   "python3 -c \"import sqlite3; n=[r[0] for r in sqlite3.connect('$DB').execute('SELECT name FROM groups')]; assert set(n)=={'Akira','Conti','REvil'}, n\""
ck "each group carries a synthetic public claim and an LLM persona" \
   "python3 -c \"import sqlite3,json; [ (json.loads(a)['demand_usd'], json.loads(b)['system_prompt']) for a,b in sqlite3.connect('$DB').execute('SELECT synthetic_public_claim,chat_persona FROM groups') ]\""
ck "the analyzer self-tests (staircase, tactics, intra + gap bluffs)" \
   "python3 '$RC/analyze.py' --selftest"
ck "the persona states its demand as already made, not as an instruction to re-open" \
   "python3 -c \"import sqlite3,json; p=[json.loads(r[0])['system_prompt'] for r in sqlite3.connect('$DB').execute('SELECT chat_persona FROM groups')]; assert all('ALREADY' in s and 'Open near' not in s for s in p)\""
ck "the chat pins group, anchor, floor and deadline server-side, and guards the replies" \
   "python3 '$HERE/../../images/ransomchat/session.py' --selftest"

# analyze the shipped sample session and confirm the teaching payoff appears
OUT="$(python3 "$RC/analyze.py" "$RC/sample-session.json" 2>/dev/null)"
ck "the sample session yields a descending offer staircase" \
   'grep -Eq "offer staircase.*900,000.*600,000.*450,000" <<< "$OUT"'
ck "it flags the price, deadline and deletion bluffs" \
   '[ "$(grep -Ec "\[price\]|\[deadline\]|\[deletion\]" <<< "$OUT")" -eq 3 ]'
ck "it surfaces the bluff in the gap vs the public leak-site posture" \
   'grep -q "bluff in the gap" <<< "$OUT"'
ck "it checks authenticity against the real corpus" \
   'grep -q "authenticity vs the real corpus" <<< "$OUT"'

echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

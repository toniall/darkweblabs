#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 12.1 — The extortion operation as two surfaces
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1)); else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
LAB="$HERE/../../lab"
CORP="$HERE/../artifacts/leak-extract/corpus"
SELF="$("$LAB" leak selftest 2>/dev/null)"
STORE="$("$LAB" leak store 2>/dev/null)"
echo; echo "Lab 12.1 — The extortion operation as two surfaces"; echo
ck "leak-lab corpus present (15 pages + 4 transcripts = 19 files)" 'test $(ls "$CORP"/*.html "$CORP"/*.txt 2>/dev/null | wc -l) -eq 19'
ck "every corpus file carries the synthetic watermark" 'test $(grep -rl "SYNTHETIC LAB DATA" "$CORP" | wc -l) -eq 19'
ck "./lab leak selftest passes offline" 'grep -q "leak self-tests passed" <<< "$SELF"'
ck "selftest covers the bluff cross-check" 'grep -Eq "cross-checking public claim against private transcript" <<< "$SELF"'
ck "./lab leak store ingests 15 pages into 14 objects" 'grep -Eq "15 fetched pages.*14 distinct" <<< "$STORE"'
ck "the unchanged victim collapses at storage" 'grep -Eq "1 byte-identical mirror collapsed" <<< "$STORE"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 8.7 — Ground truth and the scoring harness
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
SCORER="$HERE/../artifacts/range-scorer/scorer.py"
MANIFEST="$HERE/../artifacts/range-scorer/manifest.json"
SAMPLE="$HERE/../artifacts/range-scorer/sample-crawl.json"
echo; echo "Lab 8.7 — Ground truth and the scoring harness"; echo
ck "the scorer self-tests (recall/precision + clone detection)" \
   "python3 '$SCORER' --selftest"
ck "the ground-truth manifest ships and is valid JSON" \
   "python3 -m json.tool '$MANIFEST' >/dev/null"
ck "the manifest defines the logical services (answer key)" \
   "grep -q 'logical_services' '$MANIFEST'"
SCORED="$(python3 "$SCORER" "$SAMPLE" 2>/dev/null)"
ck "scoring the sample crawl reports coverage (recall)" \
   'grep -q recall <<< "$SCORED"'
ck "scoring surfaces the believed clone as a failure" \
   'grep -q FAIL <<< "$SCORED"'
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

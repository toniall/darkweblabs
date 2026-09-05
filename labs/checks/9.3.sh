#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.3 — Parsing and link extraction across networks
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
echo; echo "Lab 9.3 — Parsing and link extraction across networks"; echo
ck "the extractor self-tests (href + bare links, key material, hashing)" \
   "python3 '$CRAWLER/extract.py' --selftest"
ck "a Hyphanet key classifies by form" \
   "python3 '$CRAWLER/frontier.py' --classify 'USK@cafe/archive/0/' | grep -q hyphanet"
ck "an onion classifies as tor" \
   "python3 '$CRAWLER/frontier.py' --classify http://$(printf 'a%.0s' $(seq 56)).onion | grep -q tor"
ck "the extractor reads bare dark-web addresses, not just href" \
   "grep -q '_BARE_RE' '$CRAWLER/extract.py'"
ck "the extractor pulls key material for clone detection" \
   "grep -q 'extract_keys' '$CRAWLER/extract.py'"
ck "(host) the crawler and scorer are mounted in the workstation" \
   "docker exec darkweb-workstation test -f /opt/range-scorer/scorer.py"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

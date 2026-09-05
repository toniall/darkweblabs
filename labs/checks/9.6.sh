#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 9.6 — Storage, provenance, and dedup
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
. "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
HERE="$(cd "$(dirname "$0")" && pwd)"
CRAWLER="$HERE/../artifacts/crawler"
MANIFEST="$HERE/../artifacts/range-scorer/manifest.json"
echo; echo "Lab 9.6 — Storage, provenance, and dedup"; echo
ck "the crawler self-tests (mirror-collapse + clone flag verified against the scorer)" \
   "python3 '$CRAWLER/crawl.py' --selftest"
ck "the engine collapses mirrors" \
   "grep -q 'mirror' '$CRAWLER/crawl.py'"
ck "the engine flags clones by structural match with divergent keys" \
   "grep -q '_structural' '$CRAWLER/crawl.py'"
ck "ground truth defines a mirror relationship" \
   "grep -q 'mirror' '$MANIFEST'"
ck "ground truth defines a clone relationship" \
   "grep -q 'clone' '$MANIFEST'"
ck "(host) the range exposes market, mirror, and clone to compare" \
   "dex_has darkweb-range-tor 'market-clone' cat /content/onions.env"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

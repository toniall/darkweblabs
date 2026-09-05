#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.2 — Correlation, at toy scale
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"
CDIR="$HERE/../artifacts/correlate"
CORR="$CDIR/correlate.py"
gen_logs() {  # $1 = match | rand   -> writes /tmp/ck52/{uplink,dest}.log
  python3 - "$1" <<'PY'
import sys, random, os
mode = sys.argv[1]
rng = random.Random(0 if mode == "match" else 7)
os.makedirs("/tmp/ck52", exist_ok=True)
def cluster(centers, delay=0.0):
    o = []
    for c in centers:
        for _ in range(8):
            o.append(c + delay + rng.uniform(0, 0.15))
    return sorted(o)
if mode == "match":
    cen = [i * 1.5 for i in range(10)]
    a, b = cluster(cen), cluster(cen, 0.2)
else:
    a = cluster(sorted(rng.uniform(0, 15) for _ in range(10)))
    b = cluster(sorted(rng.uniform(0, 15) for _ in range(10)))
open("/tmp/ck52/uplink.log", "w").write("\n".join(f"{t:.4f}" for t in a))
open("/tmp/ck52/dest.log", "w").write("\n".join(f"{t:.4f}" for t in b))
PY
}
echo; echo "Lab 5.2 — Correlation, at toy scale"; echo
ck "the correlation harness is present and its correlator self-tests clean" \
   "test -f '$CDIR/observe.sh' && test -f '$CDIR/generate.sh' && test -f '$CORR' && python3 '$CORR' --selftest"
ck "a known-matching pair is reported as the same flow" \
   "gen_logs match && python3 '$CORR' /tmp/ck52/uplink.log /tmp/ck52/dest.log | grep -q 'SAME FLOW'"
ck "an unrelated pair is NOT reported as the same flow" \
   "gen_logs rand && ! python3 '$CORR' /tmp/ck52/uplink.log /tmp/ck52/dest.log | grep -q 'SAME FLOW'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

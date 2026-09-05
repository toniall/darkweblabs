#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.7 — Hardening a service you run (OnionShare is the hardened reference)
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }
HERE="$(cd "$(dirname "$0")" && pwd)"

# Resolve OnionShare's source directory INSIDE the workstation and grep there.
# Resolving it on the host is useless (onionshare_cli is not installed here), and
# a grep with no path operand silently searches the container's working
# directory instead — which is what this check used to do.
osgrep() {
  docker exec darkweb-workstation sh -c '
    d=$(python3 -c "import onionshare_cli,os;print(os.path.dirname(onionshare_cli.__file__))" 2>/dev/null) || exit 1
    [ -n "$d" ] && [ -d "$d" ] || exit 1
    grep -rqiE "$1" "$d"
  ' _ "$1"
}

echo; echo "Lab 4.7 — Hardening a service you run"; echo
ck "the hardened reference (OnionShare) sets a Content-Security-Policy" \
  "osgrep 'Content-Security-Policy'"
ck "it sets anti-sniffing / referrer hardening headers" \
  "osgrep 'nosniff|no-referrer'"
ck "the leaky contrast artifact is present for comparison" \
  "test -f '$HERE/../artifacts/leaky/server.py'"
echo; echo "  $pass passed, $fail failed"; [ "$fail" -eq 0 ]

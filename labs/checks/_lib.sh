#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | 2026
#
# labs/checks/_lib.sh — helpers shared by the lab checks. Sourced, never run.
# The leading underscore keeps it out of `./lab ci`, which globs *.sh.
#
# ─── why this file exists ────────────────────────────────────────────────────
#
# This, under `set -o pipefail`, is a race rather than a test:
#
#     docker exec <ctr> iptables -S FORWARD | grep -q '^-P FORWARD DROP'
#
# `grep -q` exits the instant it matches. If the pattern is on the FIRST line,
# grep is gone while the writer is still going, the writer takes SIGPIPE and
# exits 141, and `pipefail` reports the whole pipeline as failed — for an
# assertion that was true. With `docker exec` the writer is the Docker CLI,
# which still has stream teardown to do after the data, so the window is wide.
#
# Measured in isolation, 400 trials each:
#
#     pattern on the first line, writer still writing : 398/400 false failures
#     pattern on the last line, writer already done   :   0/400 false failures
#
# That is exactly the split seen on grokbot: Lab 2.7's `-P FORWARD DROP` (line
# one of the output) failed about 40% of runs, while the REJECT and ESTABLISHED
# assertions immediately beside it — matching later lines — never flaked once.
# Lab 5.6 nests 2.7 and inherited it; 5.7 and 6.6 nest it too and were one rule
# reordering away from the same thing.
#
# `dex_has` captures the output first and matches from a file, so nothing is
# ever writing into a closed pipe. Grade the output, not the plumbing.
#
# ─── usage ───────────────────────────────────────────────────────────────────
#
#     . "$(cd "$(dirname "$0")" && pwd)/_lib.sh"
#
#     ck "the gateway's FORWARD policy is DROP" \
#        "dex_has darkweb-gateway '^-P FORWARD DROP' iptables -S FORWARD"
#
# Patterns are extended regular expressions (grep -E). `dex_hasi` is the
# case-insensitive form. Both return non-zero — a clean FAIL, not a crash — when
# the container is missing, the command fails, or the output is empty.
#
# A pipe INSIDE a container-side `sh -c '...'` is not affected by any of this:
# that shell has no `pipefail` of its own. Those are left alone on purpose.

_CK_TMP=""

_ck_tmp() {
  if [ -z "$_CK_TMP" ]; then
    _CK_TMP="$(mktemp)" || return 1
    # shellcheck disable=SC2064
    trap 'rm -f "$_CK_TMP"' EXIT
  fi
  printf '%s' "$_CK_TMP"
}

_dex_match() {
  local ci="$1" ctr="$2" pat="$3"
  shift 3
  local out tmp rc

  out="$(docker exec "$ctr" "$@" 2>/dev/null)" || return 1
  [ -n "$out" ] || return 1

  tmp="$(_ck_tmp)" || return 1
  printf '%s\n' "$out" > "$tmp" || return 1

  if [ -n "$ci" ]; then
    grep -qEi -- "$pat" "$tmp"
  else
    grep -qE -- "$pat" "$tmp"
  fi
  rc=$?
  return "$rc"
}

# dex_has <container> <ere-pattern> <command...>
dex_has()  { _dex_match ""  "$@"; }

# dex_hasi <container> <ere-pattern> <command...>   (case-insensitive)
dex_hasi() { _dex_match "i" "$@"; }

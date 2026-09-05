#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.2 generator. RUN ON THE HOST (Ubuntu). Emits a distinctive bursty on/off
# pattern from the workstation through Tor, logging each burst time as the series
# to correlate against the uplink capture. You own both: the pattern and the wire.
set -u
OUT=/tmp/correlate; mkdir -p "$OUT"; : > "$OUT/dest.log"
BURSTS="${BURSTS:-10}"
echo "generate: sending $BURSTS bursts through Tor"
printf 'generate: sent %s bursts at t =' "$BURSTS"
for i in $(seq 1 "$BURSTS"); do
  t=$(date +%s.%N); echo "$t" >> "$OUT/dest.log"; printf ' %.1f' "$t"
  # a burst = several quick requests through the gateway SOCKS (real Tor traffic)
  docker exec darkweb-workstation sh -c \
    'for j in 1 2 3 4 5 6; do curl -s -o /dev/null --socks5-hostname 10.152.152.10:9050 --max-time 20 https://check.torproject.org/ & done; wait' 2>/dev/null
  sleep 1.5
done
echo; echo "exit    : burst times -> $OUT/dest.log"

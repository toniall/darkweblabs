#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.2 entry-side observer. RUN ON THE HOST (Ubuntu) — it needs docker.
# Captures the timestamps of Tor cells leaving the gateway's uplink.
set -u
OUT=/tmp/correlate; mkdir -p "$OUT"
DUR="${OBSERVE_SECS:-24}"
echo "observe : capturing gateway uplink (eth0) for ${DUR}s -> $OUT/uplink.log"
docker exec darkweb-gateway timeout "$DUR" tcpdump -ni eth0 -tt tcp 2>/dev/null \
  | awk '{print $1}' > "$OUT/uplink.log"
echo "observe : $(wc -l < "$OUT/uplink.log" 2>/dev/null || echo 0) packet timestamps logged"

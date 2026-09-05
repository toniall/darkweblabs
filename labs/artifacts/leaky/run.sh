#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 4.6 — start the leaky service and publish it as an onion through the gateway.
# Run this on the lab desktop; probe the printed onion from another terminal.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
GW="${LAB_GATEWAY_IP:-10.152.152.10}"
PORT="${LEAKY_PORT:-8899}"

python3 "$DIR/server.py" &
SRV=$!
sleep 1

# the address the onion must forward to (this host's real internal address)
WS_IP="$(python3 -c 'import socket,os
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.connect((os.environ.get("LAB_GATEWAY_IP","10.152.152.10"),9051))
print(s.getsockname()[0]); s.close()')"

# publish a detached onion so it outlives this control connection
resp="$(printf 'AUTHENTICATE "%s"\r\nADD_ONION NEW:ED25519-V3 Port=80,%s:%s Flags=Detach\r\nQUIT\r\n' \
        "$LAB_CONTROL_PW" "$WS_IP" "$PORT" | nc -w8 "$GW" 9051)"
onion="$(printf '%s' "$resp" | sed -n 's/^250-ServiceID=//p' | tr -d '\r')"

if [ -z "$onion" ]; then
  echo "failed to publish onion:"; printf '%s\n' "$resp"; kill "$SRV" 2>/dev/null; exit 1
fi

echo "onion: ${onion}.onion"
echo "serving on ${WS_IP}:${PORT}"
echo "probe it from another terminal, e.g.:"
echo "  curl -sI --socks5-hostname ${GW}:9050 http://${onion}.onion/"
echo "  curl -s  --socks5-hostname ${GW}:9050 http://${onion}.onion/server-status"
echo
echo "(Ctrl-C to stop the server; the detached onion lingers in Tor until it restarts.)"
trap 'kill "$SRV" 2>/dev/null' INT TERM
wait "$SRV"

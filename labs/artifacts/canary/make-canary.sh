#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 5.5 — write a DEFANGED canary document and start the beacon listener.
# The document is plain HTML whose only trick is a remote image pointed at a
# LAB-INTERNAL address. No macros, no scripts, no exploit — the mechanism only.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT=/tmp/canary; mkdir -p "$OUT"
PORT="${CANARY_PORT:-8971}"
LISTEN_IP="$(python3 -c 'import socket,os
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.connect((os.environ.get("LAB_GATEWAY_IP","10.152.152.10"),9051))
print(s.getsockname()[0]); s.close()')"

cat > "$OUT/report.html" <<HTML
<!doctype html>
<title>Quarterly Report</title>
<h1>Quarterly Report</h1>
<p>Please review the figures below.</p>
<!-- the canary: a remote image beacons the opener to a lab-internal listener -->
<img src="http://${LISTEN_IP}:${PORT}/beacon.gif?doc=q3-report" width="1" height="1" alt="">
<p>End of report.</p>
HTML

echo "listener on ${LISTEN_IP}:${PORT}"
echo "canary written to $OUT/report.html"
exec python3 "$DIR/listener.py"

#!/bin/bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Start the desktop and serve it to the browser over TLS.
#
# Three steps, all visible here: set the VNC password, start an X session, then
# bridge it to a websocket. No vendor startup framework — a failure in this file
# is a failure you can read.
set -eu

VNC_DISPLAY="${VNC_DISPLAY:-:1}"
# 1280x800 fits most laptop browser windows without scrolling on connect. Raise
# it with LAB_RESOLUTION, or leave the desktop to follow the window — noVNC now
# defaults to Remote Resizing (see the image build).
VNC_RESOLUTION="${VNC_RESOLUTION:-1280x800}"
WEB_PORT="${WEB_PORT:-6901}"
CERT=/etc/darkweb/self.pem
LAB_GATEWAY_IP="${LAB_GATEWAY_IP:-10.152.152.10}"
LAB_INTERNAL_CIDR="${LAB_INTERNAL_CIDR:-10.152.152.0/24}"
LAB_DESK_CIDR="${LAB_DESK_CIDR:-10.152.153.0/24}"
: "${VNC_PW:?VNC_PW is not set — start the stack with ./lab up, not docker compose}"

mkdir -p "$HOME/.vnc" "$HOME/Desktop" "$HOME/labs"

# ─── network ──────────────────────────────────────────────────────────────────
# Route off this host only through the gateway, resolve through it, and lock the
# desktop-access interface to inbound only. Done as root through one sudo rule;
# everything after this runs as the analyst user.
echo "[workstation] configuring network via gateway ${LAB_GATEWAY_IP}"
sudo /usr/local/sbin/darkweb-netsetup \
  "$LAB_GATEWAY_IP" "$LAB_INTERNAL_CIDR" "$LAB_DESK_CIDR"

# Probe the gateway's SOCKS port. The stack waits for the gateway to be healthy
# before starting us, so this should pass immediately; the loop only covers the
# moment just after. It turns "gateway down" into a clear line here instead of
# an opaque "Tor exited during startup" in the browser later.
gw_ok=0
for _ in $(seq 1 15); do
  if (exec 3<>"/dev/tcp/${LAB_GATEWAY_IP}/9050") 2>/dev/null; then
    exec 3<&- 2>/dev/null || true; gw_ok=1; break
  fi
  sleep 1
done
[ "$gw_ok" = 1 ] \
  && echo "[workstation] gateway SOCKS reachable at ${LAB_GATEWAY_IP}:9050" \
  || echo "[workstation] WARNING: gateway SOCKS ${LAB_GATEWAY_IP}:9050 not reachable yet" >&2

# ─── onionshare ───────────────────────────────────────────────────────────────
# Point OnionShare at the gateway's tor via its control port, so it publishes
# onion services through the existing circuit instead of starting its own tor —
# which would be Tor-over-Tor, the "Connecting to the Tor network… 10%" you see
# otherwise. Written each start so an image update or a rotated password reaches
# an existing home. With no control password, OnionShare keeps its own defaults
# (and falls back to its bundled tor).
if [ -n "${LAB_CONTROL_PW:-}" ]; then
  os_dir="$HOME/.config/onionshare"
  mkdir -p "$os_dir"
  cat > "$os_dir/onionshare.json" <<JSON
{
  "connection_type": "control_port",
  "control_port_address": "${LAB_GATEWAY_IP}",
  "control_port_port": 9051,
  "socks_address": "${LAB_GATEWAY_IP}",
  "socks_port": 9050,
  "auth_type": "password",
  "auth_password": "${LAB_CONTROL_PW}",
  "auto_connect": true,
  "bridges_enabled": false
}
JSON
  echo "[workstation] OnionShare pointed at the gateway's control port"
fi

# ─── the credential ───────────────────────────────────────────────────────────
# TigerVNC reads $HOME/.vnc/passwd and refuses it unless it is 0600.
printf '%s\n%s\n\n' "$VNC_PW" "$VNC_PW" | vncpasswd -f > "$HOME/.vnc/passwd"
chmod 600 "$HOME/.vnc/passwd"
[ -s "$HOME/.vnc/passwd" ] || { echo "[workstation] ERROR: empty passwd" >&2; exit 1; }

cp /usr/share/darkweb/xstartup "$HOME/.vnc/xstartup"
chmod +x "$HOME/.vnc/xstartup"

# Launchers, refreshed each start so an image update reaches an existing home.
cp -f /usr/share/darkweb/desktop/*.desktop "$HOME/Desktop/" 2>/dev/null || true
chmod +x "$HOME/Desktop/"*.desktop 2>/dev/null || true

# ─── X session ────────────────────────────────────────────────────────────────
echo "[workstation] starting Xvnc on $VNC_DISPLAY ($VNC_RESOLUTION)"
vncserver -kill "$VNC_DISPLAY" >/dev/null 2>&1 || true
rm -f "/tmp/.X11-unix/X${VNC_DISPLAY#:}" "/tmp/.X${VNC_DISPLAY#:}-lock"

# -localhost yes: Xvnc listens on loopback only. The browser reaches it through
# websockify below, so the raw VNC port never needs to be exposed at all.
#
# AcceptCutText / SendCutText / AcceptSetDesktopSize are what make the clipboard
# and window resizing work from the browser.
vncserver "$VNC_DISPLAY" \
  -geometry "$VNC_RESOLUTION" \
  -depth 24 \
  -localhost yes \
  -SecurityTypes VncAuth \
  -rfbauth "$HOME/.vnc/passwd" \
  -AcceptCutText=1 \
  -SendCutText=1 \
  -AcceptSetDesktopSize=1 \
  -MaxCutText=2000000 \
  < /dev/null

# Wait for Xvnc to accept connections before bridging to it.
#
# Tested with bash's own /dev/tcp rather than xdpyinfo. xdpyinfo lives in
# x11-utils, not x11-xserver-utils — installing the wrong one made this loop
# time out every time, and the exit below turned that into a crash loop: the
# container restarted, XFCE started again, and the log filled with session
# noise while nothing ever served. A dependency that only shows up as a timeout
# is worth removing entirely.
VNC_TCP_PORT=$((5900 + ${VNC_DISPLAY#:}))
ready=0
for _ in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/127.0.0.1/$VNC_TCP_PORT") 2>/dev/null; then
    exec 3<&- 2>/dev/null || true
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  echo "[workstation] ERROR: Xvnc never listened on $VNC_TCP_PORT" >&2
  tail -40 "$HOME/.vnc/"*.log 2>/dev/null >&2
  exit 1
fi
echo "[workstation] Xvnc listening on $VNC_TCP_PORT"

# TLS is optional. Default off: the desktop is reached over loopback (or an SSH
# tunnel, which is already encrypted), where plain HTTP is fine and avoids the
# browser's self-signed-certificate warning. Set LAB_TLS=on to serve HTTPS —
# do that if you publish this port beyond localhost.
LAB_TLS="${LAB_TLS:-off}"
tls_args=""
scheme="http"
if [ "$LAB_TLS" = "on" ]; then
  # Confirm the certificate is readable before websockify tries to use it. A
  # permission problem here surfaces as a TLS handshake failure in the browser,
  # which points nowhere useful.
  if [ ! -r "$CERT" ]; then
    echo "[workstation] ERROR: cannot read $CERT" >&2
    ls -la "$CERT" >&2 || true
    exit 1
  fi
  tls_args="--cert=$CERT"
  scheme="https"
fi

# Stream the session log in the background, so it appears in `docker logs`
# alongside websockify's own output.
LOG="$(ls -1t "$HOME/.vnc/"*.log 2>/dev/null | head -1 || true)"
[ -n "$LOG" ] && tail -F "$LOG" &

echo "[workstation] serving ${scheme}://0.0.0.0:${WEB_PORT} -> localhost:5901 (LAB_TLS=${LAB_TLS})"

# websockify runs in the FOREGROUND and is the container's main process.
#
# It was previously started with --daemon while the container held itself open
# tailing a log file. That meant websockify could fail — an unreadable
# certificate, a port already bound — and the container would carry on looking
# alive while serving nothing. The process that matters should be the one
# keeping the container up.
exec websockify \
  --web /usr/share/novnc \
  $tls_args \
  "0.0.0.0:${WEB_PORT}" \
  "localhost:${VNC_TCP_PORT}"

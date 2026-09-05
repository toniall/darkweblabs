#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Bring up the gateway: render tor's config for this container's address,
# install the firewall, start tor, and signal ready once it has bootstrapped.
#
# A failure in this file is a failure you can read — there is no init system
# and no vendor wrapper. tor runs in the foreground as the container's main
# process, so if it dies the container dies and restarts, rather than lingering
# healthy while carrying nothing.
set -eu

GATEWAY_IP="${LAB_GATEWAY_IP:-10.152.152.10}"
INTERNAL_CIDR="${LAB_INTERNAL_CIDR:-10.152.152.0/24}"
CONTROL_PW="${LAB_CONTROL_PW:-}"
READY=/run/darkweb/ready
TORLOG=/run/darkweb/tor.log

mkdir -p /run/darkweb
rm -f "$READY"

# ─── render torrc ─────────────────────────────────────────────────────────────
# Bind tor's ports to the internal address specifically — see the note in the
# template. If the address is ever wrong, tor fails to bind and says so, which
# is a far better failure than listening on the wrong interface silently.
#
# Control-port auth is decided here: hash the shared secret (tor is present in
# this image; the host that generated the secret may not be) into a
# HashedControlPassword line. With no secret, fall back to cookie auth, which
# confines the control port to processes inside this container.
if [ -n "$CONTROL_PW" ]; then
  HASHED="$(tor --hash-password "$CONTROL_PW" 2>/dev/null | grep '^16:' | tail -1)"
  if [ -n "$HASHED" ]; then
    CONTROL_AUTH="HashedControlPassword $HASHED"
    echo "[gateway] control port: password authentication enabled"
  else
    CONTROL_AUTH="CookieAuthentication 1"
    echo "[gateway] WARNING: could not hash control password; using cookie auth" >&2
  fi
else
  CONTROL_AUTH="CookieAuthentication 1"
  echo "[gateway] control port: no shared secret, cookie auth (local only)"
fi

sed -e "s#__GATEWAY_IP__#${GATEWAY_IP}#g" \
    -e "s#__CONTROL_AUTH__#${CONTROL_AUTH}#g" \
    /etc/tor/torrc.template > /etc/tor/torrc
echo "[gateway] tor will bind its ports on ${GATEWAY_IP}"

# ─── firewall first ───────────────────────────────────────────────────────────
# Installed before tor starts, so there is never a window in which the gateway
# is routing without the rules. (The workstation waits for readiness below in
# any case, but ordering the box's own protection first costs nothing.)
LAB_INTERNAL_CIDR="$INTERNAL_CIDR" LAB_GATEWAY_IP="$GATEWAY_IP" \
  /usr/local/bin/rules.sh

# ─── data directory ───────────────────────────────────────────────────────────
# The compose file mounts a named volume at /var/lib/tor, and a fresh volume is
# owned by root. That mount happens at run time, AFTER the image build, so the
# chown baked into the Dockerfile is masked by it: tor runs as the tor user,
# cannot write its DataDirectory, and exits at once — a restart loop that prints
# almost nothing. Fixing ownership here, as root, before tor starts, is the
# reliable place. tor also refuses a DataDirectory that others can read.
chown -R tor:tor /var/lib/tor
chmod 700 /var/lib/tor

# ─── tor ──────────────────────────────────────────────────────────────────────
# Wait until Docker has actually assigned our internal address before tor tries
# to bind to it — binding to an address that is not up yet fails hard.
for _ in $(seq 1 10); do
  ip -4 addr show | grep -q "inet ${GATEWAY_IP}/" && break
  sleep 1
done

# tor logs to stdout; tee it so `docker logs darkweb-gateway` shows it live AND
# the readiness watcher can grep it. The log lives under /run, not in the tor
# data volume, so nothing here depends on that volume's permissions.
: > "$TORLOG"
( tor -f /etc/tor/torrc 2>&1 | tee -a "$TORLOG" ) &
TOR_PID=$!

# Signal readiness the moment tor reaches 100%, whenever that is — a slow first
# bootstrap on a poor link should still end in a ready gateway, not a timeout.
( until grep -q "Bootstrapped 100%" "$TORLOG" 2>/dev/null; do
    kill -0 "$TOR_PID" 2>/dev/null || exit 0   # tor pipeline ended; leave un-ready
    sleep 2
  done
  touch "$READY"
  echo "[gateway] tor bootstrapped to 100% — ready" ) &

# Keep the container alive on tor itself. If it ends, the log above shows why.
wait "$TOR_PID" || true
echo "[gateway] tor process ended" >&2

#!/bin/bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Launch Tor Browser on a workstation whose traffic is already torified.
#
# The problem this solves
# ----------------------
# Tor Browser normally starts its own tor. Here every connection this host makes
# is already redirected through the gateway's tor, so that daemon's traffic
# would itself be tunnelled — a second circuit inside the first. Tor over Tor is
# slower and
# worse for anonymity, not better: it does not add a layer, it makes your path
# unusual. The Tor Project advises against it.
#
# Environment variables alone are not enough on the 16.0 series. The browser
# still tries to reach a control port to confirm Tor is healthy, our tor uses
# cookie authentication, and that cookie lives in the tor container's
# filesystem — which this container cannot read. The check fails and you get
# "Tor exited during startup".
#
# So the launcher is disabled in the profile as well, and the browser is pointed
# straight at the gateway's SOCKS port. This is the arrangement Whonix uses.
set -eu

TB=/opt/tor-browser
PROFILE="$TB/Browser/TorBrowser/Data/Browser/profile.default"
# The gateway is a separate host now, not a shared namespace, so SOCKS lives at
# its internal address. Passed through from the container environment; the
# default matches compose.
SOCKS_HOST="${LAB_GATEWAY_IP:-10.152.152.10}"
SOCKS_PORT=9050
# The gateway's control port. Giving the launcher a control port it can reach is
# what turns "Tor exited during startup" into a working monitor with New Circuit
# / New Identity. Authenticated with the shared password; empty means fall back
# to the old no-control behaviour.
CONTROL_HOST="$SOCKS_HOST"
CONTROL_PORT=9051
CONTROL_PW="${LAB_CONTROL_PW:-}"

# ─── stale lock ───────────────────────────────────────────────────────────────
# "Tor Browser is already running, but is not responding" after a container is
# stopped rather than shut down cleanly.
if ! pgrep -f "$TB/Browser/firefox" >/dev/null 2>&1; then
  rm -f "$PROFILE/lock" "$PROFILE/.parentlock" 2>/dev/null || true
fi

# ─── profile ──────────────────────────────────────────────────────────────────
# Written on every launch, so an image update reaches an existing profile.
mkdir -p "$PROFILE"
cat > "$PROFILE/user.js" <<PREFS
// Managed by the lab. Do not edit — rewritten at every launch.

// Do not start a second tor. The gateway already provides one. Point the
// launcher at the gateway's control port so it can confirm tor is up and drive
// it (New Circuit, New Identity) instead of reporting a startup failure.
user_pref("extensions.torlauncher.start_tor", false);
user_pref("extensions.torlauncher.prompt_at_startup", false);
user_pref("extensions.torlauncher.control_port_auto", false);
user_pref("extensions.torlauncher.control_host", "$CONTROL_HOST");
user_pref("extensions.torlauncher.control_port", $CONTROL_PORT);

// Skip the connection assistant: there is nothing to configure, and it cannot
// verify a tor it does not control.
user_pref("torbrowser.settings.quickstart.enabled", true);
user_pref("network.proxy.allow_hijacking_localhost", true);

// Talk to the gateway's SOCKS port, and resolve names through it so hostnames
// never leak to a local resolver.
user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "$SOCKS_HOST");
user_pref("network.proxy.socks_port", $SOCKS_PORT);
user_pref("network.proxy.socks_version", 5);
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.dns.blockDotOnion", false);

// The lab desktop is a single X session; a second instance confuses the lock.
user_pref("browser.tabs.warnOnClose", false);
PREFS

# ─── environment ──────────────────────────────────────────────────────────────
# The documented contract for running Tor Browser against an external tor: skip
# launching one, and hand it the SOCKS and control endpoints. With a control
# port reachable we do NOT skip the control-port test — we want the launcher to
# use it. The password is passed quoted, the form tor's AUTHENTICATE expects;
# the lab generates it alphanumeric so no escaping is needed.
export TOR_SKIP_LAUNCH=1
export TOR_NO_DISPLAY_NETWORK_SETTINGS=1
export TOR_SOCKS_HOST="$SOCKS_HOST"
export TOR_SOCKS_PORT="$SOCKS_PORT"
if [ -n "$CONTROL_PW" ]; then
  export TOR_CONTROL_HOST="$CONTROL_HOST"
  export TOR_CONTROL_PORT="$CONTROL_PORT"
  export TOR_CONTROL_PASSWD="\"$CONTROL_PW\""
  echo "[tor-browser] gateway tor: socks ${SOCKS_HOST}:${SOCKS_PORT}, control ${CONTROL_HOST}:${CONTROL_PORT}"
else
  # No shared secret — nothing to connect to, so suppress the control-port test.
  export TOR_SKIP_CONTROLPORTTEST=1
  echo "[tor-browser] gateway tor: socks ${SOCKS_HOST}:${SOCKS_PORT} (no control port)"
fi

exec "$TB/Browser/start-tor-browser" --detach "$@"

#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | 2026
# i2pd testnet router entrypoint — Chapter 6.
#
# A CLOSED I2P testnet has no live reseed server, so the routers must be each
# other's bootstrap. Three things have to be true at once, and missing any one of
# them produces the same symptom: routers healthy, /seed full of routerInfos, and
# `known routers: 0` forever.
#
#   1. A published routerInfo must carry a REACHABLE address. Left to
#      auto-detect, a minted RI often has no NTCP2/SSU2 address at all. Peers
#      import it and drop it, because a router advertising no address is one
#      nobody can dial. We pin host= to the container's real eth0.
#   2. i2pd must be willing to talk to RFC1918 peers. `reservedrange = true` is
#      the default and blacklists 10.x, which is every router here. Handled in
#      i2pd.conf.tmpl.
#   3. reseed.zip must exist, and be COMPLETE, before i2pd starts. i2pd reseeds
#      at most once per process, so a zip that appears afterwards is never read.
#
# Hence the order: mint an identity pinned to our address, publish it, wait for a
# real quorum of peers, build the bundle atomically, start i2pd, and restart once
# if the NetDB is still empty — the restart IS the retry.
set -u

NETID="${I2P_NETID:-42}"
FLOODFILL="${I2P_FLOODFILL:-false}"
SEED="${I2P_SEED_DIR:-/seed}"
DATA="${I2P_DATADIR:-/home/i2pd/data}"
NAME="$(hostname)"

START_DELAY="${I2P_START_DELAY:-0}"   # floodfills 0, plain routers ~45s
PEERS_MIN="${I2P_PEERS_MIN:-2}"       # two peers is a bootstrap; one dead-ends
PEERS_WANT="${I2P_PEERS_WANT:-4}"     # prefer all five published
SEED_WAIT="${I2P_SEED_WAIT:-180}"
NETDB_GRACE="${I2P_NETDB_GRACE:-180}"

mkdir -p "$DATA" "$SEED" "$DATA/netDb"

# ── our address on the testnet ───────────────────────────────────────────────
# Three ways, because this must not depend on which tools the base image ships.
detect_ip() {
  ip -4 -o addr show scope global 2>/dev/null \
    | awk '{split($4,a,"/"); print a[1]; exit}' | grep -E '^[0-9]+(\.[0-9]+){3}$' && return 0
  hostname -i 2>/dev/null \
    | tr ' ' '\n' | grep -E '^[0-9]+(\.[0-9]+){3}$' | grep -v '^127\.' | head -1 && return 0
  getent hosts "$(hostname)" 2>/dev/null \
    | awk '{print $1; exit}' | grep -E '^[0-9]+(\.[0-9]+){3}$' && return 0
  return 1
}
HOST_IP="${I2P_HOST_IP:-$(detect_ip)}"
if [ -z "$HOST_IP" ]; then
  echo "i2p-testnet: $NAME could not determine its own IPv4 address" >&2
  exit 1
fi

conf="$DATA/i2pd.conf"
render_conf() {
  sed -e "s/@NETID@/$NETID/" \
      -e "s/@FLOODFILL@/$FLOODFILL/" \
      -e "s/@HOST@/$HOST_IP/" \
      -e "s#@ZIPFILE@#$SEED/reseed.zip#" \
      /opt/lab/i2pd.conf.tmpl > "$conf"
}
render_conf

echo "i2p-testnet: $NAME  netid=$NETID  floodfill=$FLOODFILL  host=$HOST_IP  seed=$SEED"

# ── helpers ──────────────────────────────────────────────────────────────────
# Peers are files, not a glob assumption: on this i2pd they land as
# netDb/rX/routerInfo-<hash>.dat, so count *.dat anywhere under netDb.
netdb_size() { find "$DATA/netDb" -type f -name '*.dat' 2>/dev/null | wc -l; }

peer_count() { ls "$SEED"/routerInfo-*.dat 2>/dev/null | grep -cv "routerInfo-$NAME.dat"; }

# Atomic and per-process, so two routers writing at once cannot hand i2pd a
# half-written archive to reseed from.
build_bundle() {
  ls "$SEED"/routerInfo-*.dat >/dev/null 2>&1 || return 1
  tmp="$SEED/reseed.zip.tmp.$$"
  ( cd "$SEED" && zip -q -j -X "$tmp" routerInfo-*.dat ) 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$SEED/reseed.zip" 2>/dev/null || { rm -f "$tmp"; return 1; }
  return 0
}

publish() {
  [ -f "$DATA/router.info" ] || return 1
  cp -f "$DATA/router.info" "$SEED/routerInfo-$NAME.dat" 2>/dev/null || return 1
  printf '%s' "$HOST_IP" > "$DATA/.published_ip"
  return 0
}

mint_identity() {
  echo "i2p-testnet: $NAME minting a router identity on $HOST_IP"
  rm -f "$DATA/router.info" "$DATA/router.keys"
  i2pd --datadir="$DATA" --conf="$conf" &
  mint=$!
  n=0
  while [ ! -f "$DATA/router.info" ] && [ "$n" -lt 60 ]; do sleep 1; n=$((n+1)); done
  kill "$mint" 2>/dev/null
  wait "$mint" 2>/dev/null
  sleep 2
}

# ── 0) stagger, so floodfills are publishing before the routers arrive ───────
if [ "$START_DELAY" -gt 0 ] 2>/dev/null; then
  echo "i2p-testnet: $NAME waiting ${START_DELAY}s for the floodfills"
  sleep "$START_DELAY"
fi

# ── 1) identity, pinned to our current address ───────────────────────────────
# A persisted identity minted against a DIFFERENT IP is worse than none: it
# publishes an address nobody can reach. Remint when the address has moved.
published_ip="$(cat "$DATA/.published_ip" 2>/dev/null || true)"
if [ ! -f "$DATA/router.info" ]; then
  mint_identity
elif [ "$published_ip" != "$HOST_IP" ]; then
  echo "i2p-testnet: $NAME address changed ($published_ip -> $HOST_IP), reminting"
  mint_identity
fi

publish && echo "i2p-testnet: $NAME published routerInfo ($HOST_IP)"

# ── 2) wait for a real quorum, then build the bundle BEFORE starting ─────────
waited=0
while [ "$waited" -lt "$SEED_WAIT" ]; do
  have="$(peer_count)"
  [ "$have" -ge "$PEERS_WANT" ] && break
  if [ "$have" -ge "$PEERS_MIN" ] && [ "$waited" -ge 45 ]; then break; fi
  sleep 5; waited=$((waited+5))
done
have="$(peer_count)"
if build_bundle; then
  echo "i2p-testnet: $NAME reseed.zip built from $have peer(s) before start"
else
  echo "i2p-testnet: $NAME could not build reseed.zip (peers: $have)" >&2
fi

# ── 3) start i2pd against a bundle that exists and is complete ───────────────
i2pd --datadir="$DATA" --conf="$conf" &
I2PD_PID=$!

# ── 4) one restart as the retry, then keep the bundle fresh ─────────────────
elapsed=0
reseeded=0
while kill -0 "$I2PD_PID" 2>/dev/null; do
  publish >/dev/null 2>&1
  build_bundle
  if [ "$reseeded" -eq 0 ] && [ "$elapsed" -ge "$NETDB_GRACE" ] \
     && [ "$(netdb_size)" -eq 0 ] && [ "$(peer_count)" -ge "$PEERS_MIN" ]; then
    echo "i2p-testnet: $NAME NetDB empty after ${NETDB_GRACE}s, restarting to reseed"
    reseeded=1
    kill "$I2PD_PID" 2>/dev/null; wait "$I2PD_PID" 2>/dev/null
    i2pd --datadir="$DATA" --conf="$conf" &
    I2PD_PID=$!
    elapsed=0
    continue
  fi
  sleep 10
  elapsed=$((elapsed+10))
done

wait "$I2PD_PID"

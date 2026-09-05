#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Hyphanet darknet testnet node entrypoint — Chapter 7.
#
# SCAFFOLD / STATIC-CHECKED ONLY. The darknet noderef exchange below is the
# fragile, version-sensitive piece this chapter flags: the exact way a node
# exports its reference and adds a friend's reference differs across Hyphanet
# versions and may need FCP (AddPeer) rather than file placement. Validate on
# the host with `./lab check 7.1`. Hyphanet also settles slowly — allow minutes.
set -u

OPENNET="${FN_OPENNET:-false}"
SEED="${FN_SEED_DIR:-/seed}"
STORE="${FN_STORE_SIZE:-512M}"
DATA="${FN_DATADIR:-/data}"
FN_HOME="${FN_HOME:-/opt/hyphanet}"
NAME="$(hostname)"

mkdir -p "$DATA" "$SEED"

# 1) render freenet.ini from the template + environment
conf="$DATA/freenet.ini"
sed -e "s/@STORE@/$STORE/" /opt/lab/freenet.ini.tmpl > "$conf"
echo "hyphanet-testnet: $NAME  opennet=$OPENNET  store=$STORE  seed=$SEED"

# 2) launch the node. Provisioning must have placed freenet.jar under $FN_HOME
#    (see the Dockerfile note); this is where the host completes the setup.
if [ -f "$FN_HOME/freenet.jar" ]; then
  ( cd "$DATA" && java -jar "$FN_HOME/freenet.jar" "$conf" ) &
  NODE_PID=$!
else
  echo "hyphanet-testnet: $FN_HOME/freenet.jar not provisioned — see Dockerfile." >&2
  echo "  This node cannot start until the Hyphanet runtime is placed on the host." >&2
  # keep the container alive so the operator can exec in and finish provisioning
  NODE_PID=""
fi

# 3) darknet friend exchange: publish our node reference, then add peers' refs.
#    Hyphanet writes its darknet ref once the node is up; the exact filename is
#    version-specific — adjust the glob if your version differs.
published=""
while :; do
  if [ -z "$published" ]; then
    ref="$(ls "$DATA"/*.fref "$DATA"/node-*.fref 2>/dev/null | head -n1)"
    if [ -n "$ref" ] && [ -f "$ref" ]; then
      cp -f "$ref" "$SEED/$NAME.fref" && published=1 \
        && echo "hyphanet-testnet: $NAME published its darknet noderef"
    fi
  fi
  # (host-side) add every OTHER node's ref as a darknet friend. Placement here is
  # illustrative; some versions require FCP AddPeer instead of a drop directory.
  for f in "$SEED"/*.fref; do
    [ -f "$f" ] || continue
    case "$f" in *"/$NAME.fref") continue ;; esac
    cp -f "$f" "$DATA/friend-$(basename "$f")" 2>/dev/null || true
  done
  [ -n "$NODE_PID" ] && ! kill -0 "$NODE_PID" 2>/dev/null && break
  sleep 15
done

[ -n "$NODE_PID" ] && wait "$NODE_PID"

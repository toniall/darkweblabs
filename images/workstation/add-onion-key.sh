#!/bin/bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Add Onion Key — register a client-auth private key with the gateway's tor, so
# a keyed OnionShare service opens in Tor Browser without touching a terminal.
#
# Why this exists: on the gateway/workstation split the onion descriptor is
# fetched by the GATEWAY's tor, not the browser's, so Tor Browser never fires
# its built-in "enter your key" prompt — you just get a generic connection
# error. This sends ONION_CLIENT_AUTH_ADD to the gateway's control port, which
# is exactly what that prompt would do, aimed at the tor that actually needs
# the key. The key is registered in memory for this session; if you restart the
# lab, run this again.
#
# Encoding note: OnionShare shows the private key base32-encoded (its key_str
# uses b32encode), but ONION_CLIENT_AUTH_ADD expects base64 — so we convert.
set -u

GW="${LAB_GATEWAY_IP:-10.152.152.10}"
PORT=9051
PW="${LAB_CONTROL_PW:-}"

err() { zenity --error --width=400 --title="Add Onion Key" --text="$1" 2>/dev/null; exit 1; }

command -v zenity >/dev/null 2>&1 || { echo "zenity missing" >&2; exit 1; }
[ -n "$PW" ] || err "No control password in the environment.\nStart the lab with ./lab up (not plain docker compose)."

form="$(zenity --forms --width=470 --title="Add Onion Key" \
  --text="Register a private key for a keyed onion.\nIn OnionShare, click <b>Reveal</b> on the private key and copy it." \
  --add-entry="Onion address (….onion)" \
  --add-entry="Private key" 2>/dev/null)" || exit 0

onion="$(printf '%s' "$form" | cut -d'|' -f1 | tr -d '[:space:]' | sed 's/\.onion$//')"
key="$(printf '%s'  "$form" | cut -d'|' -f2 | tr -d '[:space:]' | sed 's/^descriptor:x25519://; s/^x25519://')"

[ -n "$onion" ] && [ -n "$key" ] || err "Both the onion address and the private key are required."

# base32 (as OnionShare shows it) -> base64 (as the control port expects)
key_b64="$(python3 -c '
import base64, sys
k = sys.argv[1].strip().upper()
k += "=" * ((8 - len(k) % 8) % 8)
sys.stdout.write(base64.b64encode(base64.b32decode(k)).decode())
' "$key" 2>/dev/null)" || key_b64=""
[ -n "$key_b64" ] || err "That does not look like a valid OnionShare private key.\nCopy it exactly, using the Reveal button."

resp="$(printf 'AUTHENTICATE "%s"\r\nONION_CLIENT_AUTH_ADD %s x25519:%s\r\nQUIT\r\n' \
          "$PW" "$onion" "$key_b64" | nc -w6 "$GW" "$PORT" 2>/dev/null | tr -d '\r')"

auth="$(printf '%s\n' "$resp" | sed -n '1p')"
add="$(printf  '%s\n' "$resp" | sed -n '2p')"

case "$auth" in
  "250 OK") ;;
  "") err "No response from the gateway control port (${GW}:${PORT}).\nIs the gateway healthy?" ;;
  *)  err "Control-port authentication failed:\n${auth}" ;;
esac

case "$add" in
  250*|251*) zenity --info --width=470 --title="Add Onion Key" \
      --text="Key registered with the gateway.\n<small>tor: ${add}</small>\n\nNow open the onion in a <b>new Tor Browser tab</b> — paste the address into a fresh tab rather than reloading the page that already failed, so Tor fetches it again with the key." 2>/dev/null ;;
  *) zenity --error --width=540 --title="Add Onion Key" \
      --text="The gateway did not accept the key.\n\nControl-port response:\n<tt>${resp:-<no response>}</tt>\n\nCopy this text and send it back so it can be fixed." 2>/dev/null; exit 1 ;;
esac

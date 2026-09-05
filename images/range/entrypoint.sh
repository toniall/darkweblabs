#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Generate the range's watermarked content, then publish an onion per service.
# Mirror shares the market's backend (same content, different onion); the clone
# uses the clone web backend (altered pgp+btc). Onion keys are not persisted.
set -eu

SEED_DIR="${RANGE_SEED_DIR:-/content}"
WEB="${RANGE_WEB:-range-web}"
WEB_CLONE="${RANGE_WEB_CLONE:-range-web-clone}"

echo "[range] generating synthetic watermarked content into ${SEED_DIR}"
python3 /opt/seed.py --out "${SEED_DIR}"

# service  ->  backend:port   (market-mirror shares market's backend)
MAP="directory ${WEB}:8080
market ${WEB}:8081
forum ${WEB}:8082
leak ${WEB}:8083
paste ${WEB}:8084
market-mirror ${WEB}:8081
market-clone ${WEB_CLONE}:8091"

TORRC=/etc/tor/torrc
mkdir -p /var/lib/tor /etc/tor
{
    echo "User tor"
    echo "SocksPort 0"
    echo "DataDirectory /var/lib/tor"
} > "${TORRC}"

echo "${MAP}" | while IFS=' ' read -r name backend; do
    [ -n "${name}" ] || continue
    dir="/var/lib/tor/range-${name}"
    mkdir -p "${dir}"
    chmod 700 "${dir}"
    {
        echo "HiddenServiceDir ${dir}"
        echo "HiddenServiceVersion 3"
        echo "HiddenServicePort 80 ${backend}"
    } >> "${TORRC}"
done
chown -R tor:tor /var/lib/tor

echo "[range] starting tor; publishing onion services (ephemeral keys)"
tor -f "${TORRC}" &
TOR_PID=$!

# once each hostname exists, record service=onion for ./lab range list
ENVF="${SEED_DIR}/onions.env"
: > "${ENVF}"
echo "${MAP}" | while IFS=' ' read -r name backend; do
    [ -n "${name}" ] || continue
    hn="/var/lib/tor/range-${name}/hostname"
    tries=0
    while [ ! -s "${hn}" ] && [ "${tries}" -lt 60 ]; do
        sleep 2
        tries=$((tries + 1))
    done
    if [ -s "${hn}" ]; then
        echo "${name}=$(cat "${hn}")" >> "${ENVF}"
    else
        echo "${name}=pending" >> "${ENVF}"
    fi
done
echo "[range] published services recorded in ${ENVF}"

wait "${TOR_PID}"

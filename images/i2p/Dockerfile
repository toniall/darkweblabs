# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# I2P testnet router — Chapter 6.
#
# Real i2pd on the official image, with a *testnet* bootstrap layered on top:
# a custom netid plus a shared routerInfo seed bundle, instead of live reseeding.
#
# STATIC-CHECKED ONLY during authoring. Converging a closed I2P testnet is the
# most host- and version-sensitive part of the whole lab: the seed timing and the
# reseed mechanism below use real i2pd options but have not been run in CI here.
# Validate on the target host with `./lab check 6.1`, and expect to tune the seed
# loop per i2pd version.
FROM purplei2p/i2pd:latest

USER root
# The entrypoint is POSIX sh (busybox ash on the Alpine-based image), so no bash
# is required. `zip` is, to build the reseed bundle the routers share; busybox
# already provides wget for the compose healthcheck. The apt fallback covers a
# Debian-based i2pd image if you swap the FROM line.
# iproute2 for `ip addr`: the entrypoint pins the router's published host= to the
# container's real eth0 address, and busybox's `ip` applet is not always built in.
RUN apk add --no-cache zip iproute2 2>/dev/null \
 || (apt-get update && apt-get install -y --no-install-recommends zip iproute2 && rm -rf /var/lib/apt/lists/*)

COPY i2pd.conf.tmpl /opt/lab/i2pd.conf.tmpl
COPY entrypoint.sh  /opt/lab/entrypoint.sh
RUN chmod +x /opt/lab/entrypoint.sh

# Runs as root in the lab so it can write both the data dir and the shared /seed
# volume without a uid dance — acceptable for a throwaway testnet, not for prod.
ENTRYPOINT ["/opt/lab/entrypoint.sh"]

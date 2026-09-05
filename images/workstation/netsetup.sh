#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Root network setup for the workstation. Installed at /usr/local/sbin and run
# once from the (unprivileged) entrypoint via a single NOPASSWD sudo rule, so
# the desktop itself never runs as root but the three things that need root do.
#
#   darkweb-netsetup <gateway_ip> <internal_cidr> <desk_cidr>
#
# What it does, and why each part matters for a workstation that must not leak:
#
#   1. Default route via the gateway. Docker points it at whichever bridge it
#      pleases; we make the gateway the only way off this host.
#   2. Resolver = the gateway. Its DNSPort is redirected into Tor, so lookups
#      resolve over Tor instead of leaking to a public resolver.
#   3. Egress lock on the desktop-access interface. That bridge exists only to
#      carry the inbound noVNC session; if the workstation could open outbound
#      connections on it, it would be a path to the internet around Tor. Replies
#      to the session are allowed; anything the workstation initiates there is
#      rejected.
set -eu

GATEWAY_IP="${1:?gateway ip}"
INTERNAL_CIDR="${2:?internal cidr}"
DESK_CIDR="${3:?desk cidr}"

echo "[netsetup] default route via ${GATEWAY_IP}"
ip route replace default via "$GATEWAY_IP"

echo "[netsetup] resolver -> ${GATEWAY_IP} (redirected into tor)"
printf 'nameserver %s\n' "$GATEWAY_IP" > /etc/resolv.conf

# The line above replaces Docker's embedded resolver (127.0.0.11), so every name
# this container looks up now goes to Tor's DNSPort — which is the point, and
# which also means container names stop resolving: Tor has no idea what
# "gateway" is. Pin the one name the lab refers to by word rather than address.
# labs/artifacts/crawler/crawl_live.py defaults to socks5h://gateway:9050, and
# `./lab range fetch` uses the same target.
grep -q '[[:space:]]gateway$' /etc/hosts || printf '%s gateway\n' "$GATEWAY_IP" >> /etc/hosts

# Find the interface on the desk subnet by its address prefix — interface names
# are not stable across Docker runs, the subnet is.
DESK_PREFIX="$(echo "$DESK_CIDR" | cut -d/ -f1 | cut -d. -f1-3)."
DESK_IF="$(ip -o -4 addr show | awk -v p="$DESK_PREFIX" 'index($4,p)==1 {print $2; exit}')"

if [ -n "${DESK_IF:-}" ]; then
  echo "[netsetup] egress lock on ${DESK_IF} (inbound desktop only)"
  iptables -C OUTPUT -o "$DESK_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null \
    || iptables -A OUTPUT -o "$DESK_IF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  iptables -C OUTPUT -o "$DESK_IF" -j REJECT 2>/dev/null \
    || iptables -A OUTPUT -o "$DESK_IF" -j REJECT
else
  # Not fatal — but say so loudly, because a missing lock is a silent leak path.
  echo "[netsetup] WARNING: no interface found on ${DESK_CIDR}; egress lock NOT applied" >&2
fi

echo "[netsetup] done"

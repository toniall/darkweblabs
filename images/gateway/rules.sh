#!/bin/sh
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Force every TCP connection and DNS lookup that ARRIVES FROM THE WORKSTATION
# through Tor, and reject anything that cannot go through it.
#
# This is the routed-gateway form of the rules. In V4 the workstation shared
# tor's network namespace, so the rules lived in OUTPUT and had to exempt tor's
# own traffic by uid. Here the workstation is a separate host whose default
# route is this gateway, so its traffic arrives to be routed: we work in
# PREROUTING (redirect it into tor) and FORWARD (reject whatever tor cannot
# carry). tor's own connections are generated locally and never traverse
# PREROUTING, so there is no uid to guess and no exemption to get wrong.
set -eu

TRANS_PORT=9040
DNS_PORT=5353
GATEWAY_IP="${LAB_GATEWAY_IP:-10.152.152.10}"
INTERNAL_CIDR="${LAB_INTERNAL_CIDR:-10.152.152.0/24}"

# ─── start clean ──────────────────────────────────────────────────────────────
# This container's netns has its own tables — Docker's rules live on the host,
# not here — so flushing the chains we manage is safe and keeps a restart from
# stacking duplicate rules.
iptables -t nat -F PREROUTING
iptables -F FORWARD

# Fail closed at the policy, not only at the last rule. The explicit REJECT below
# is what the reader sees when a packet is refused; this is what catches anything
# that reaches FORWARD by a path the rules below do not describe. Both, on
# purpose: the policy is the guarantee, the REJECT is the explanation.
iptables -P FORWARD DROP

# ─── redirect the workstation's traffic into tor ──────────────────────────────
# Matched by SOURCE (the internal subnet), not by interface name: Docker does
# not promise which of eth0/eth1 is the internal one, but the address is fixed.

# DNS first, whatever nameserver it was aimed at — including this gateway. Name
# lookups must go through Tor's resolver, or a hostname leaks to a local one.
iptables -t nat -A PREROUTING -s "$INTERNAL_CIDR" -p udp --dport 53 \
  -j REDIRECT --to-ports "$DNS_PORT"
iptables -t nat -A PREROUTING -s "$INTERNAL_CIDR" -p tcp --dport 53 \
  -j REDIRECT --to-ports "$DNS_PORT"

# The trap worth naming: Tor Browser and proxychains connect to this gateway's
# SOCKS port (…:9050) EXPLICITLY. Those packets are TCP to the gateway's own
# address. Without the next rule the blanket TCP redirect below would send them
# to the TransPort instead, and SOCKS would appear dead while transparent
# proxying still worked — a confusing half-broken state. So: TCP addressed to
# the gateway itself returns unmolested and reaches SOCKS (and the control
# port). DNS to the gateway was already handled above, so it is not caught here.
iptables -t nat -A PREROUTING -s "$INTERNAL_CIDR" -d "$GATEWAY_IP" -p tcp -j RETURN

# Everything else the workstation opens: transparently into tor.
iptables -t nat -A PREROUTING -s "$INTERNAL_CIDR" -p tcp --syn \
  -j REDIRECT --to-ports "$TRANS_PORT"

# ─── fail closed ──────────────────────────────────────────────────────────────
# Legitimate clearnet traffic was redirected above and is now delivered locally
# to tor, so it never reaches FORWARD. Workstation-to-portal traffic is on the
# same subnet and is never routed here either. That leaves FORWARD carrying only
# things that must NOT leave — ICMP to the internet, stray UDP, anything tor
# cannot carry — so reject it. A ping timing out here is the design working.
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -j REJECT --reject-with icmp-port-unreachable

# ─── prove it ─────────────────────────────────────────────────────────────────
# A rule set that matches nothing looks identical to one that works until you
# try to use it. Confirm the TransPort redirect is actually present.
if ! iptables -t nat -C PREROUTING -s "$INTERNAL_CIDR" -p tcp --syn \
       -j REDIRECT --to-ports "$TRANS_PORT" 2>/dev/null; then
  echo "[gateway] ERROR: TransPort redirect did not install" >&2
  exit 1
fi

echo "[gateway] nat PREROUTING:"
iptables -t nat -L PREROUTING -n -v | sed 's/^/  /'
echo "[gateway] filter FORWARD:"
iptables -L FORWARD -n -v | sed 's/^/  /'
echo "[gateway] rules installed — workstation traffic is torified or rejected"

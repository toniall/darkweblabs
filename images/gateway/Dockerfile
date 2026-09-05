# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# darkweb-lab-gateway — tor + the transparent-proxy firewall, in one container
#
# V4 kept these apart: dockurr/tor ran the daemon, and a one-shot sidecar
# installed the rules into its namespace, so the published image stayed
# unmodified. This revision folds them together. The gateway is now dual-homed —
# one foot on the external bridge (the real Tor network), one on the internal
# bridge the workstation lives behind — and it is the workstation's router.
#
# The cost of folding: we build tor ourselves rather than run a stock image, so
# "unmodified upstream" is no longer the claim. The gain: one container instead
# of two, no PID-namespace sharing, and — because the redirect now happens in
# PREROUTING on traffic ARRIVING from the workstation, never in OUTPUT — no need
# to guess tor's uid to exempt its own traffic. tor's own connections are
# locally generated and the PREROUTING rules never see them.
FROM alpine:3.20

# tor: the daemon.  iptables: the rules.  iproute2: `ip` for reading our own
# address and, in the workstation, replacing the default route.  tcpdump: so the
# Chapter 2 labs (and the 5.1 check) can watch the uplink from inside the gateway
# and prove nothing leaks around Tor — the gateway is the one place that traffic
# is visible in the clear before tor carries it.
RUN apk add --no-cache tor iptables iproute2 tcpdump

COPY torrc /etc/tor/torrc.template
COPY rules.sh /usr/local/bin/rules.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/rules.sh /usr/local/bin/entrypoint.sh \
    && mkdir -p /run/darkweb /var/lib/tor \
    && chown -R tor:tor /var/lib/tor

# Ready is written only after tor bootstraps AND the rules load — see
# entrypoint.sh. The workstation's depends_on waits for this.
HEALTHCHECK --interval=10s --timeout=5s --start-period=120s --retries=30 \
  CMD test -f /run/darkweb/ready || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

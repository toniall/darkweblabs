# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Hyphanet (Fred) darknet testnet node — Chapter 7.
#
# SCAFFOLD / STATIC-CHECKED ONLY, and the most host-sensitive image in the lab.
# Unlike i2pd (which has an official image), Hyphanet has no canonical container:
# the node (historically "Freenet REference Daemon", Fred) is a Java app normally
# set up by an installer that also fetches dependencies and seednodes on first run.
# This Dockerfile provisions a plausible runtime, but the release URL, jar name,
# and dependency set MUST be confirmed for the current Hyphanet version on your
# host. Validate with `./lab check 7.1`; expect to complete provisioning here.
FROM eclipse-temurin:21-jre

# tools: wget/unzip to fetch the release, zip to share noderefs, procps for the
# entrypoint's liveness loop
RUN apt-get update \
 && apt-get install -y --no-install-recommends wget unzip zip procps ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Provision the Hyphanet runtime. Point this at the release you intend to run;
# the official releases live under github.com/hyphanet/fred/releases. Left as a
# build arg so it is explicit and overridable — do NOT assume this default is
# current.
ARG HYPHANET_RELEASE_URL="https://github.com/hyphanet/fred/releases/latest"
ENV FN_HOME=/opt/hyphanet
RUN useradd -m -d /home/hyphanet hyphanet && mkdir -p "$FN_HOME" /data \
 && chown -R hyphanet:hyphanet "$FN_HOME" /data
# NOTE: the actual jar + libs fetch/build is intentionally left for the host to
# complete against a pinned release — provisioning Fred reproducibly is the
# fragile step this chapter flags. Place freenet.jar (+ libs) under $FN_HOME.

COPY freenet.ini.tmpl /opt/lab/freenet.ini.tmpl
COPY entrypoint.sh    /opt/lab/entrypoint.sh
RUN chmod +x /opt/lab/entrypoint.sh

USER hyphanet
WORKDIR /data
ENTRYPOINT ["/opt/lab/entrypoint.sh"]

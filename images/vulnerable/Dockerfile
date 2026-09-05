# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
#
# THE COUNTEREXAMPLE, for Lab 1.5. Build it, read its history, throw it away.
#
# This image is deliberately wrong. It reproduces, in miniature, the two mistakes
# the Volume 1 workstation image shipped with: a credential set at build time,
# and passwordless sudo baked into a layer. Nothing in the lab stack runs it —
# it exists so you can point `docker history` at something and watch the secrets
# fall out.
#
# It is built from alpine rather than the real desktop image so the lesson costs
# you five seconds instead of ten minutes. The mistakes are what matter, and they
# are identical on any base.
#
#   docker build -t darkweb-lab-workstation:1.0-vulnerable images/vulnerable
#   docker history --no-trunc --format '{{.CreatedBy}}' \
#       darkweb-lab-workstation:1.0-vulnerable | head -30
#   docker image rm darkweb-lab-workstation:1.0-vulnerable
#
# DO NOT copy any line below into anything you intend to run.

FROM alpine:3.20

RUN apk add --no-cache sudo shadow

# MISTAKE 1. A password set as a build-time ENV. This is recorded in the layer
# metadata permanently. Overriding it at runtime changes the running process and
# nothing else: the original value ships to everyone who pulls the image.
ENV VNC_PW=D@rkW3b

RUN adduser -D darkweb

# MISTAKE 2. Passwordless sudo written into a layer. Immutable and additive: a
# later RUN that deletes this file does not remove it from the earlier layer,
# and `docker save` hands the whole stack to anyone who asks.
RUN echo "darkweb ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/darkweb

CMD ["sh", "-c", "echo 'This image is a teaching counterexample. Do not run it as anything.'"]

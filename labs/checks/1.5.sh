#!/usr/bin/env bash
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Lab 1.5 — Image provenance
# The gateway and workstation images are built on your own machine from
# Dockerfiles you can read — no registry account to compromise, no tag to move.
# The gateway now runs Tor from its own image (not a stock one). The portal is
# the exception: stock nginx, pulled by digest.
set -uo pipefail
pass=0; fail=0
ck() { if eval "$2" >/dev/null 2>&1; then echo "  PASS  $1"; pass=$((pass+1));
       else echo "  FAIL  $1"; fail=$((fail+1)); fi; }

imgs() { docker image ls --format '{{.Repository}}:{{.Tag}}'; }

# The tag the stack actually builds, read from compose.yml so a version bump
# cannot strand this check on a tag that no longer exists. Override with
# LAB_IMAGE_TAG if you are testing a side build.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TAG="${LAB_IMAGE_TAG:-$(sed -n 's/^[[:space:]]*image:[[:space:]]*darkweb-lab-gateway:\([0-9A-Za-z._-]*\).*/\1/p' "$ROOT/compose.yml" | head -1)}"
TAG="${TAG:-5.0}"

# A locally built image can still carry a RepoDigests entry — buildx writes one,
# and it is unqualified (darkweb-lab-gateway@sha256:...). A pulled image's digest
# is registry-qualified (docker.io/library/nginx@sha256:...). Judge on the
# qualification, not on the digest merely existing.
not_pulled() {
  ! docker inspect "$1" -f '{{range .RepoDigests}}{{println .}}{{end}}' 2>/dev/null \
    | sed '/^$/d' | cut -d@ -f1 | grep -q '/'
}

echo
echo "Lab 1.5 — Image provenance  (tag $TAG)"
echo

ck "gateway image is built locally"     "imgs | grep -q darkweb-lab-gateway:$TAG"
ck "workstation image is built locally" "imgs | grep -q darkweb-lab-workstation:$TAG"

echo
ck "gateway image was NOT pulled from a registry"     "not_pulled darkweb-lab-gateway:$TAG"
ck "workstation image was NOT pulled from a registry" "not_pulled darkweb-lab-workstation:$TAG"

echo
ck "the gateway runs Tor from its own image" \
   "docker exec darkweb-gateway which tor"
ck "the gateway's Tor listens on the internal interface" \
   "docker exec darkweb-gateway sh -c 'netstat -ltn 2>/dev/null || ss -ltn' | grep -q 10.152.152.10:9050"

echo
# The portal is the honest exception: stock image, pulled.
ck "the portal runs a stock nginx image"  "docker inspect darkweb-portal -f '{{.Config.Image}}' | grep -q nginx"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]

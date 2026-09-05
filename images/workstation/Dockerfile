# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# darkweb-lab-workstation — the analyst desktop
#
# XFCE + TigerVNC + noVNC, every piece from Ubuntu's own repositories.
#
# The previous build used KasmVNC. It performs better, but its branding lives in
# places that are awkward to reach — inlined data URIs, a webpack bundle, a
# symlinked web root — and several rounds of replacing it left a vendor logo on
# the connect screen and the control bar. noVNC's interface is a plain directory
# of files we own outright: nothing to strip, nothing hidden in a bundle.
#
# The trade-off is honest: noVNC is slower over a distant link. Everything else
# here is simpler for it.

# 24.04 LTS, pinned by date. Supported to 2029.
ARG BASE_IMAGE="ubuntu:noble-20260509.1"
FROM $BASE_IMAGE

# Some base images set a non-root user. Every step below writes to /etc and
# /usr, so reset explicitly rather than inheriting whatever the base left.
USER root

ARG LAB_USER=darkweb
ARG LAB_UID=1000
# The analyst account is in the sudo group (below), because Chapter 2 has you
# install tools over Tor (nmap, proxychains) and run privileged scans. That
# membership is useless without a password to authenticate to sudo, so set one.
# This grants no privilege the sudo-group membership does not already imply — it
# only makes it usable — and the box is localhost-only with no route out but Tor.
# Override at build with --build-arg LAB_SUDO_PW=... ; `./lab creds` prints it.
ARG LAB_SUDO_PW=darkweb

# UTC, not a local zone: a container reporting your timezone narrows the set of
# people you could be. Chapter 2 tests for it.
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    TZ=UTC \
    DISPLAY=:1 \
    HOME=/home/darkweb

# ─── desktop and remote access ────────────────────────────────────────────────
# dbus-x11 matters — without it XFCE starts but menus misbehave.
#
# tigervnc-tools supplies vncconfig, which is what makes copy and paste work:
# it bridges the X selections to the VNC protocol. Without it the clipboard
# panel in noVNC appears to work and moves nothing.
#
# autocutsel keeps PRIMARY and CLIPBOARD in step, so middle-click paste and
# Ctrl+V agree with each other.
RUN apt-get update && apt-get install -y --no-install-recommends \
        xfce4 xfce4-terminal xfce4-goodies dbus-x11 \
        x11-xserver-utils x11-utils \
        xfonts-base fonts-dejavu-core \
        tigervnc-standalone-server tigervnc-common tigervnc-tools \
        autocutsel xclip xsel \
        novnc websockify \
        openssl ca-certificates curl wget gnupg xz-utils librsvg2-bin \
        python3 python3-venv \
        sudo nano vim tmux jq git \
    && rm -rf /var/lib/apt/lists/*

# ─── analyst tooling ──────────────────────────────────────────────────────────
# tcpdump and iproute2 are here because the Chapter 2 verification labs capture
# from inside this container.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tcpdump iproute2 iptables iputils-ping dnsutils netcat-openbsd \
        tor torsocks proxychains4 \
        onionshare onionshare-cli \
        openssh-client gpg xdg-utils zenity \
    && rm -rf /var/lib/apt/lists/*

# proxychains and torsocks point at the gateway's SOCKS port. The gateway is a
# separate host now — not a shared namespace — so that is its internal address,
# baked in here at build time. Note proxy_dns: without it, hostnames resolve
# outside the tunnel — the leak Chapter 2 hunts for. Lab 2.7 contrasts this with
# the gateway's transparent redirect and shows that proxychains is behavioural
# (a tool can ignore it) where the gateway's rules are structural (it cannot).
ARG GATEWAY_IP=10.152.152.10
RUN printf '%s\n' \
      'strict_chain' \
      'proxy_dns' \
      'remote_dns_subnet 224' \
      'tcp_read_time_out 15000' \
      'tcp_connect_time_out 8000' \
      '[ProxyList]' \
      "socks5 ${GATEWAY_IP} 9050" \
    > /etc/proxychains4.conf; \
    printf 'TorAddress %s\nTorPort 9050\n' "${GATEWAY_IP}" >> /etc/tor/torsocks.conf

# ── OnionShare behind the gateway ─────────────────────────────────────────────
# OnionShare assumes tor is on the same host: it binds its web server to
# localhost and tells tor to forward the onion to localhost. Here tor is on the
# gateway and the server is on the workstation, so "localhost" from the gateway
# is the gateway's own loopback — empty — and the service publishes but answers
# nothing. Two changes, both mirroring how OnionShare already runs on Whonix:
#   1. This marker file is OnionShare's own signal (web.py, upstream #220) to
#      bind the server to 0.0.0.0, so it listens on the workstation's internal
#      address and not just loopback.
#   2. onionshare-fix.py repoints the onion's target from loopback to the
#      workstation's address. On real Whonix the gateway's onion-grater rewrites
#      this; the lab talks to the control port directly, so we set it at source.
ARG WS_IP=10.152.152.11
RUN mkdir -p /usr/share/anon-ws-base-files \
    && : > /usr/share/anon-ws-base-files/workstation
COPY onionshare-fix.py /usr/local/sbin/onionshare-fix.py
# Chat needs a working WebSocket backend. OnionShare asks for gevent, but
# gevent-websocket is unmaintained and stalls on Python 3.12 (the chat socket
# upgrades to 101, then pumps no frames). Install simple-websocket — flask-
# socketio's maintained WebSocket path — and onionshare-fix.py repoints chat at
# threading + simple-websocket, which works on 3.12.
RUN set -eux; \
    if ! command -v pip3 >/dev/null 2>&1; then \
      apt-get update; \
      apt-get install -y --no-install-recommends python3-pip; \
      rm -rf /var/lib/apt/lists/*; \
    fi; \
    pip3 install --break-system-packages --no-cache-dir simple-websocket
RUN python3 /usr/local/sbin/onionshare-fix.py "${WS_IP}"

# One-click helper to register a keyed onion's private key with the gateway's
# tor (the split setup means Tor Browser's own key prompt never fires). A
# desktop launcher (desktop/add-onion-key.desktop) runs it; zenity draws the
# dialog, nc talks to the control port.
COPY add-onion-key.sh /usr/local/bin/add-onion-key
RUN chmod +x /usr/local/bin/add-onion-key

# ─── Tor Browser ──────────────────────────────────────────────────────────────
# Channel by architecture, because the Tor Project's official builds force it:
# the STABLE channel ships linux-x86_64 only, and linux-aarch64 exists only on
# the ALPHA channel (16.0aX). So x86_64 hosts get stable; arm64 hosts get the
# alpha — the only real Tor Browser the Tor Project publishes for ARM. (There
# are unofficial third-party arm64 stable builds, but a dark-web lab should not
# fetch its browser from a non-Tor-Project source.) Alphas are pruned from the
# mirror once superseded, so the arm64 pin will need moving; check what a
# version ships before pinning:
#   curl -s https://dist.torproject.org/torbrowser/15.0.19/ | grep -o 'tor-browser-linux[^"]*'
ARG TB_VERSION_X86=15.0.21
ARG TB_VERSION_ARM=16.0a9
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) tbarch=linux-x86_64;  tbver="${TB_VERSION_X86}" ;; \
      arm64) tbarch=linux-aarch64; tbver="${TB_VERSION_ARM}" ;; \
      *) echo "no Tor Browser build for $arch" >&2; exit 1 ;; \
    esac; \
    echo "Tor Browser: ${tbarch} ${tbver}"; \
    mkdir -p /opt; \
    cd /tmp; \
    file="tor-browser-${tbarch}-${tbver}.tar.xz"; \
    curl -fsSLO "https://dist.torproject.org/torbrowser/${tbver}/${file}"; \
    tar -xf "$file" -C /opt; \
    rm -f "$file"; \
    chmod -R a+rX /opt/tor-browser; \
    test -x /opt/tor-browser/Browser/start-tor-browser

COPY tor-browser-launch.sh /usr/local/bin/tor-browser
RUN chmod +x /usr/local/bin/tor-browser

# Firefox from Mozilla's own repository. Ubuntu's package is a snap stub that
# cannot run in a container, so the repo is not optional.
#
# Two browsers, deliberately. Both exit through Tor — this container's only
# route off the host is the gateway, which redirects transparently — so what
# separates them is fingerprint resistance, which Chapter 2 measures.
RUN set -eux; \
    install -d -m 0755 /etc/apt/keyrings; \
    curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg \
      -o /etc/apt/keyrings/packages.mozilla.org.asc; \
    echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] \
https://packages.mozilla.org/apt mozilla main" \
      > /etc/apt/sources.list.d/mozilla.list; \
    printf 'Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n' \
      > /etc/apt/preferences.d/mozilla; \
    apt-get update; \
    apt-get install -y --no-install-recommends firefox; \
    rm -rf /var/lib/apt/lists/*

# ─── the analyst account ──────────────────────────────────────────────────────
# Ubuntu 24.04 ships a default `ubuntu` account at uid/gid 1000 — new in noble,
# and it collides with ours. Remove whatever holds 1000 before claiming it,
# rather than picking a different uid: 1000 is what bind-mounted files from the
# host are owned by, so moving off it creates permission problems later.
RUN set -eux; \
    if getent passwd "$LAB_UID" >/dev/null; then \
      existing="$(getent passwd "$LAB_UID" | cut -d: -f1)"; \
      echo "removing default account '$existing' holding uid $LAB_UID"; \
      userdel -r "$existing" 2>/dev/null || userdel "$existing"; \
    fi; \
    if getent group "$LAB_UID" >/dev/null; then \
      groupdel "$(getent group "$LAB_UID" | cut -d: -f1)" 2>/dev/null || true; \
    fi; \
    groupadd -g "$LAB_UID" "$LAB_USER"; \
    useradd -m -u "$LAB_UID" -g "$LAB_UID" -s /bin/bash "$LAB_USER"; \
    usermod -aG sudo "$LAB_USER"; \
    printf '%s:%s\n' "$LAB_USER" "$LAB_SUDO_PW" | chpasswd; \
    mkdir -p /evidence; \
    chown -R "$LAB_USER:$LAB_USER" "/home/$LAB_USER" /evidence /opt/tor-browser; \
    id "$LAB_USER"

# ─── TLS certificate ──────────────────────────────────────────────────────────
# Generated per build, never committed. A PEM in a public repository publishes
# its private key — every reader would share one — and a text-mode transfer
# corrupts it in a way that fails TLS with no useful message.
RUN set -eux; \
    mkdir -p /etc/darkweb; \
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
      -subj "/CN=darkweb-lab" \
      -keyout /etc/darkweb/key.pem -out /etc/darkweb/cert.pem 2>/dev/null; \
    cat /etc/darkweb/cert.pem /etc/darkweb/key.pem > /etc/darkweb/self.pem; \
    chmod 640 /etc/darkweb/self.pem; \
    chgrp "$LAB_USER" /etc/darkweb/self.pem; \
    openssl x509 -in /etc/darkweb/self.pem -noout -subject

# ─── branding ─────────────────────────────────────────────────────────────────
# noVNC keeps its interface in a plain directory: app/images/ for the marks,
# vnc.html for the page. Everything is a file we can overwrite — no data URIs
# inlined into a bundle, no symlinked web root, nothing hidden.
ARG LAB_BRAND_URL=https://abrandao.net
ARG LAB_BRAND_TITLE="Dark Web Lab"
COPY brandin[g]/ /usr/share/darkweb/
COPY rebrand.py /usr/local/bin/rebrand.py
RUN set -eux; \
    if [ -f /usr/share/darkweb/background.png ]; then \
      install -Dm644 /usr/share/darkweb/background.png \
        /usr/share/backgrounds/darkweb.png; \
      echo "wallpaper installed"; \
    fi; \
    if [ -f /usr/share/darkweb/logo.svg ]; then \
      LAB_BRAND_URL="$LAB_BRAND_URL" \
      LAB_BRAND_TITLE="$LAB_BRAND_TITLE" \
      python3 /usr/local/bin/rebrand.py /usr/share/novnc /usr/share/darkweb; \
    fi

# Rasterize the launcher icons to PNG. xfdesktop renders an Icon= only if
# gdk-pixbuf can load it; the image ships librsvg2-bin (the rsvg-convert CLI)
# but NOT librsvg2-common (the gdk-pixbuf SVG loader), so an SVG Icon= falls
# back to a generic page icon. PNG needs no loader, so convert here and point
# the .desktop files at the PNGs. rsvg-convert is already installed.
RUN set -eux; \
    for name in lab-portal onionshare add-onion-key; do \
      svg="/usr/share/darkweb/${name}.svg"; \
      [ -f "$svg" ] || continue; \
      rsvg-convert -w 128 -h 128 "$svg" -o "/usr/share/darkweb/${name}.png"; \
      test -s "/usr/share/darkweb/${name}.png"; \
      echo "icon: ${name}.png"; \
    done

# ─── clipboard sync ───────────────────────────────────────────────────────────
# noVNC's own clipboard is an explicit panel, because a page cannot silently
# read the system clipboard. This restores automatic sync in browsers that
# permit it — Chrome, after one permission prompt — and degrades to
# Ctrl+Shift+V elsewhere. Firefox has no clipboard-read permission at all.
#
# Set LAB_CLIPBOARD_AUTO=0 to keep the panel-only behaviour.
ARG LAB_CLIPBOARD_AUTO=1

# noVNC's interface is an ES module. app/ui.js ends with `export default UI;`
# and never assigns anything to window, so nothing outside the module graph can
# reach the live connection — verified against noVNC 1.3, 1.4 and 1.5. A script
# injected into the page loads, runs, finds no RFB object and fails silently.
# One appended line opens the seam. Statements after `export default` are legal
# in a module, so appending survives a package upgrade better than a targeted
# substitution would.
RUN set -eux; \
    printf '\n/* darkweb: expose the UI singleton so the clipboard bridge can reach RFB */\nwindow.UI = UI;\n' \
      >> /usr/share/novnc/app/ui.js; \
    grep -q 'window.UI = UI' /usr/share/novnc/app/ui.js; \
    echo "UI singleton exposed"

COPY novnc/darkweb-clipboard.js /usr/share/novnc/app/darkweb-clipboard.js
# Inject two things ahead of noVNC's module: the clipboard-auto flag and a
# default scaling mode. Setting 'resize' to 'remote' — unless the reader has
# already chosen — makes the desktop follow the browser window instead of
# arriving at a fixed size that needs scrolling, which is the "too big on
# connect" complaint. noVNC's Settings panel still switches it per session
# (None / Local Scaling / Remote Resizing). A lower default geometry in
# entrypoint.sh handles the case where a client cannot resize at all.
#
# The rewrite is done in Python, not sed: the string carries quotes and braces
# that make sed's own quoting a hazard, and python3 is already installed.
RUN set -eux; \
    auto="$([ "$LAB_CLIPBOARD_AUTO" = "1" ] && echo true || echo false)"; \
    inject="<script>window.DARKWEB_CLIPBOARD_AUTO = ${auto}; try{if(!localStorage.getItem('resize'))localStorage.setItem('resize','remote');}catch(e){}</script><script src=\"app/darkweb-clipboard.js\"></script>"; \
    for page in /usr/share/novnc/vnc.html /usr/share/novnc/index.html; do \
      [ -f "$page" ] || continue; \
      grep -q 'darkweb-clipboard' "$page" && continue; \
      python3 -c 'import sys; p,inj=sys.argv[1],sys.argv[2]; h=open(p,encoding="utf-8").read(); open(p,"w",encoding="utf-8").write(h.replace("</body>","  "+inj+"\n</body>",1))' "$page" "$inject"; \
      grep -q 'darkweb-clipboard' "$page" \
        || { echo "ERROR: could not inject into $page" >&2; exit 1; }; \
      echo "clipboard + resize default injected into $(basename "$page")"; \
    done

# noVNC ships vnc.html but no index, so websockify serves the web root as a bare
# directory listing — the "loads a file list instead of the desktop" problem.
# Add an index that sends the root straight to the client, carrying any query
# string (autoconnect, password, resize) and hash through untouched.
RUN printf '%s\n' \
      '<!doctype html>' \
      '<html><head><meta charset="utf-8"><title>Lab desktop</title>' \
      '<script>location.replace("vnc.html" + location.search + location.hash);</script>' \
      '<meta http-equiv="refresh" content="0; url=vnc.html">' \
      '</head><body>Loading the lab desktop&hellip;</body></html>' \
      > /usr/share/novnc/index.html

COPY desktop/ /usr/share/darkweb/desktop/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY xstartup /usr/share/darkweb/xstartup
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/share/darkweb/xstartup

# Root network setup, reachable from the unprivileged entrypoint through exactly
# one NOPASSWD rule and nothing else. The desktop runs as the analyst user; only
# the default route, the resolver and the egress lock touch root — see
# netsetup.sh. visudo -c fails the build on a malformed rule rather than at run
# time, where it would present as sudo silently prompting for a password.
COPY netsetup.sh /usr/local/sbin/darkweb-netsetup
RUN set -eux; \
    chmod 0755 /usr/local/sbin/darkweb-netsetup; \
    printf '%s\n' \
      '# darkweb: let the analyst user run only the network setup as root' \
      "${LAB_USER} ALL=(root) NOPASSWD: /usr/local/sbin/darkweb-netsetup" \
      > /etc/sudoers.d/darkweb-netsetup; \
    chmod 0440 /etc/sudoers.d/darkweb-netsetup; \
    visudo -cf /etc/sudoers.d/darkweb-netsetup

USER $LAB_UID
WORKDIR $HOME
EXPOSE 6901
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

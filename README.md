# Unlock the Secrets of the DARK WEB: Threat Intelligence and Hands-On Labs

**Volume 2: the lab environment.**

This repository is the command half of the book. It carries everything you need to
build and run the labs: the container images, the engines each chapter has you
write, the synthetic range they are graded against, and a local site that lists
every command under the same lab number the book uses.

The book carries everything: the reasoning behind each step, what it will get
wrong and how you would know, and every command box with its expected output.
You can work through a whole chapter from the printed page alone. The site is
the same commands in a form you can copy from, which is what it is for.

Five labs are on the book's pages but not on the public site: Labs 11.8, 12.8,
12.9 and 14.8, which run against real archived data, and Chapter 15, the
capstone that chains every engine into a single report. The code and data for
all five ship here, so they run as soon as you have the book.

**Licensing.** The lab code is MIT (see `LICENSE`). The companion site and the
book text are proprietary and licensed separately; their terms travel with the
site package.

A two-container Whonix: a **gateway** that runs tor and forces everything through
it, and a **workstation** whose only route off the host is that gateway. The
workstation has no path to the clearnet; anything tor cannot carry is rejected,
not leaked.

| Component | Image | Why |
|---|---|---|
| Gateway | built on `alpine` | runs tor, dual-homed, and installs the transparent-proxy firewall |
| Workstation | built on `ubuntu:noble` | XFCE + TigerVNC + noVNC, all from Ubuntu's repos; routes through the gateway |
| Portal | `nginx:alpine` | serves `site/`, internal network only |

Earlier revisions split the gateway into a stock `dockurr/tor` container plus a
one-shot rules sidecar. This one folds them into a single gateway image; see
`images/gateway/`.

## Quick start

    chmod +x lab labs/checks/*.sh \
             images/gateway/entrypoint.sh images/gateway/rules.sh \
             images/workstation/entrypoint.sh images/workstation/netsetup.sh \
             images/workstation/xstartup
    ./lab doctor
    ./lab selftest
    ./lab up base
    ./lab creds

On a VPS, tunnel rather than publishing the port:

    ssh -L 6901:127.0.0.1:6901 you@your-vps

## Copy and paste

Through the clipboard panel in the noVNC sidebar, in both directions:

- **Host to lab**, copy on your machine, open the panel, paste into the box.
  The text is now on the lab's clipboard; paste normally inside the desktop.
- **Lab to host**, copy inside the desktop. It appears in the panel. Select it
  there and copy, and it is on your machine's clipboard.

### Automatic sync

The lab also injects a small script that syncs the clipboard without the panel.

| Browser | Host to lab | Lab to host |
|---|---|---|
| **Chrome** (recommended) | automatic, after one prompt | automatic |
| Firefox | `Ctrl+Shift+V` | automatic |
| Safari | `Ctrl+Shift+V` | usually automatic |

Chrome implements a `clipboard-read` permission; Firefox deliberately does not,
and requires a genuine paste gesture instead. Both positions are defensible.
`Ctrl+V` is forwarded to the remote desktop, which is why the shortcut carries
the extra modifier.

Granting clipboard read means the lab page can see everything you copy while
that tab has focus. Convenient, and a real widening of what the container
observes about the host; the panel grants nothing and always works. Build
without automatic sync:

    LAB_CLIPBOARD_AUTO=0 ./lab rebuild

Three pieces make that work, and all three are needed:

- `vncconfig -nowin` in the session, which bridges the X selections to the VNC
  protocol. Without it the panel is just a text box that owns nothing.
- `AcceptCutText` / `SendCutText` on the server, permission for clipboard
  traffic in each direction.
- `autocutsel` on PRIMARY and CLIPBOARD, because X has two selections and they are not
  the same. This keeps middle-click paste and Ctrl+V in agreement.

## Notes

**The desktop follows your browser window.** noVNC defaults to Remote Resizing,
so the desktop resizes to fit rather than arriving oversized. Switch it in the
noVNC Settings panel (None / Local Scaling / Remote Resizing), or pin a fixed
size with `LAB_RESOLUTION=1600x900 ./lab up base`.

**Tor Browser and OnionShare use the gateway's tor, not their own.** The gateway
exposes a password-authenticated control port on its internal interface, and both
apps are pointed at it, so Tor Browser can confirm bootstrap and offer New
Circuit, and OnionShare can publish onion services, without either launching a
second tor (Tor-over-Tor). The control password is generated per-stack into
`.env` like the desktop password, and never committed. Worth naming: a reachable
control port lets a compromised workstation issue control commands to tor. It
still cannot make tor leak (the redirect and fail-closed rules are unchanged),
but it is more power than the workstation otherwise has. The hardened form is a
control-port filter (onion-grater) that whitelists only the commands these apps
use, and, usefully, rewrites onion targets the way step 2 below does by hand;
that is a Part II topic.

**Hosting an onion service from the workstation takes two steps, because the
gateway never reaches into the workstation by default.** OnionShare would bind
its server to loopback and tell tor to forward there, but "there" is the
gateway's own loopback, which is empty, so the service publishes yet answers
nothing. The image fixes both halves the way Whonix does: it drops the marker
file OnionShare checks for (so the server binds on all interfaces) and repoints
the onion's target at the workstation's internal address (so the gateway's tor
forwards to the real server). Connecting *to* other onions never needed this;
that is outbound and works like clearnet.

**OnionShare chat is patched for modern Python.** OnionShare drives its chat
over a WebSocket via gevent-websocket, which is unmaintained and stalls on
Python 3.12 (the socket upgrades but delivers no messages). The image installs
simple-websocket and repoints chat at flask-socketio's maintained threading
path, so messages flow. This is an image-side patch of OnionShare's own code, so
revisit it when the OnionShare package updates.

**The desktop is plain HTTP on loopback by default** (`LAB_TLS=off`), so the
browser shows no certificate warning: the connection is local, or tunnelled over
SSH which is already encrypted. If you publish port 6901 beyond localhost, run
`LAB_TLS=on ./lab up base` to serve HTTPS with the self-signed certificate
instead.

**The web desktop opens at the root.** `https://127.0.0.1:6901/` redirects to
the noVNC client; you do not need to append `/vnc.html`.

**Tor Browser channel is chosen by architecture.** x86_64 gets the **stable**
release (`15.0.21`); arm64 gets the **alpha** (`16.0a9`), because the Tor
Project publishes `linux-aarch64` only on the alpha channel; there is no
official stable ARM build. Override with `LAB_TB_VERSION_X86` /
`LAB_TB_VERSION_ARM`; alphas are pruned from the mirror once superseded, so the
ARM pin will need moving over time.

**Reaching a keyed OnionShare service.** OnionShare locks a service to a private
key by default. On the gateway/workstation split, Tor Browser's built-in "enter
your key" prompt does not fire (the gateway's tor fetches the descriptor, not
the browser), so you register the key yourself with a desktop shortcut, **Add Onion
Key**, does this in one step: click it, paste the `.onion` and the key from
OnionShare's **Reveal** button, and reload. For a classroom exercise where the
key is a distraction, tick **"This is a public OnionShare service"** to drop the
key requirement entirely; teach the key as the secure default and use public
mode for the walkthrough.

**OnionShare's chat mode is a known limitation on current Python; use the other
modes.** Share, Receive, and Website all work over the onion; chat connects but
does not deliver messages. The cause is upstream, not the lab: OnionShare's chat
pushes messages over a WebSocket using `gevent` and the **unmaintained**
`gevent-websocket` (no release since ~2017), which stalls on Python 3.12
(Ubuntu noble). The socket completes its `101 Switching Protocols` upgrade, then
the server never sends a frame, so nothing you type reaches the room. This hits
OnionShare chat on a plain Ubuntu 24.04 host too, gateway or not; every other
part of the transport is verified end to end. For the book, demonstrate
OnionShare with share / receive / website (the core dark-web-intel use cases),
and cover chat conceptually; it's a clean real-world example of how an
abandoned async dependency breaks a feature on a newer interpreter.

**`ping` will fail from the workstation, and that is correct.** Tor carries TCP
only; ICMP cannot be routed through it, so the gateway rejects it. Test with
`curl https://check.torproject.org/api/ip` instead.

## Continuous integration

Before you push, run everything that needs no Docker:

```sh
./lab ci
```

This runs the repo self-test, every engine's offline self-test, and every
Docker-free lab check, and exits non-zero if anything has drifted. The same
command runs in GitHub Actions on every push (`.github/workflows/ci.yml`),
alongside a second job that builds the container images fresh and smoke-tests the
tools the labs depend on (for example, that the gateway can capture its uplink
and that the workstation's analyst account has a usable sudo password).

## License

This repository is source-available but not open source. You may clone and run
the labs for personal, non-commercial study; redistribution, commercial use, and
distributing derivative works are not permitted. See [LICENSE](LICENSE) for the
full terms.

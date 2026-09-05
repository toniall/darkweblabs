#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Replace noVNC's branding with the lab's own.

Far simpler than the equivalent for KasmVNC, and worth saying why: noVNC keeps
its interface in a plain directory of files. Every mark is a file we can
overwrite. Nothing is inlined as a data URI in a webpack bundle, and the web
root is not behind a symlink — the two things that made the previous attempt
report success while leaving a vendor logo on screen.

Handles:
  app/images/*.svg          the control-bar and connect-screen marks
  app/images/icons/*.png    favicon and PWA sizes, named  novnc-<N>x<N>.png
  vnc.html, index.html      page title, any remaining product name
  package.json, manifests   metadata

Reports every file touched, and exits non-zero if it changed nothing.
"""
import base64
import os
import re
import subprocess
import sys

WWW = os.path.realpath(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/novnc")
BRAND = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/darkweb"
SITE = os.environ.get("LAB_BRAND_URL", "https://abrandao.net")
TITLE = os.environ.get("LAB_BRAND_TITLE", "Dark Web Lab")

logo_svg = os.path.join(BRAND, "logo.svg")
icon_svg = os.path.join(BRAND, "icon.svg")
if not os.path.isdir(WWW):
    sys.exit(f"[rebrand] no web root at {WWW}")
if not os.path.isfile(logo_svg):
    print("[rebrand] no logo.svg supplied — nothing to do")
    sys.exit(0)
if not os.path.isfile(icon_svg):
    icon_svg = logo_svg

changed = {"icons": 0, "text": 0}

HAVE_RSVG = subprocess.run(["sh", "-c", "command -v rsvg-convert"],
                           capture_output=True).returncode == 0
if not HAVE_RSVG:
    print("[rebrand] WARN: rsvg-convert missing — PNG icons left alone",
          file=sys.stderr)

VIEWBOX = re.compile(r'viewBox\s*=\s*["\']([\d.\-\s]+)["\']', re.I)
SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.I)


def squarify(src):
    """Letterbox a wide wordmark into a square canvas rather than squashing it.

    The wordmark is 260x48; rasterising that into a 96x96 favicon with -w 96
    -h 96 would compress it to a third of its height.
    """
    try:
        with open(src, "r", encoding="utf-8") as f:
            text = f.read()
        vb = VIEWBOX.search(text)
        if not vb:
            return src
        _x, _y, w, h = (float(v) for v in vb.group(1).split())
        if abs(w - h) < 1:
            return src
        side = max(w, h)
        dx, dy = (side - w) / 2, (side - h) / 2
        inner = SVG_OPEN.sub("", text, count=1).rsplit("</svg>", 1)[0]
        out = "/tmp/square-icon.svg"
        with open(out, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'viewBox="0 0 {side} {side}" width="{side}" '
                    f'height="{side}"><g transform="translate({dx},{dy})">'
                    f'{inner}</g></svg>')
        print(f"[rebrand] icon source letterboxed {w:g}x{h:g} -> {side:g}²")
        return out
    except Exception as exc:                              # noqa: BLE001
        print(f"[rebrand] WARN: squarify failed: {exc}", file=sys.stderr)
        return src


def rasterise(src, size):
    if not HAVE_RSVG:
        return None
    try:
        return subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), src],
            check=True, capture_output=True).stdout
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"[rebrand] WARN: rasterise failed: {exc}", file=sys.stderr)
        return None


icon_square = squarify(icon_svg)

# ── images ────────────────────────────────────────────────────────────────────
with open(logo_svg, "rb") as f:
    logo_data = f.read()

for root, _dirs, files in os.walk(WWW):
    for name in files:
        path = os.path.join(root, name)
        rel = os.path.relpath(path, WWW)
        low = name.lower()

        if low.endswith(".svg"):
            # Every SVG under app/images is a brand mark in noVNC; the control
            # icons live in app/images/ too but are referenced by name, so only
            # replace ones that look like product marks.
            if re.search(r"(novnc|logo|brand|icon)", low):
                with open(path, "wb") as f:
                    f.write(logo_data)
                changed["icons"] += 1
                print(f"[rebrand] svg    {rel}")
        elif low.endswith((".png", ".ico")):
            if not re.search(r"(novnc|logo|brand|icon|favicon)", low):
                continue
            m = re.search(r"(\d+)x(\d+)", name)
            size = int(m.group(1)) if m else 96
            data = rasterise(icon_square, size)
            if data:
                with open(path, "wb") as f:
                    f.write(data)
                changed["icons"] += 1
                print(f"[rebrand] png    {rel} ({size}px)")

# ── text ──────────────────────────────────────────────────────────────────────
TITLE_RE = re.compile(r"<title>[^<]*</title>", re.I)
NOVNC_URL = re.compile(r"https?://(?:www\.)?novnc\.com[^\"'\s)]*")

for root, _dirs, files in os.walk(WWW):
    for name in files:
        if not name.lower().endswith((".html", ".json", ".webmanifest")):
            continue
        path = os.path.join(root, name)
        try:
            with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
                text = original = f.read()
        except OSError:
            continue

        text = TITLE_RE.sub(f"<title>{TITLE}</title>", text)
        text = NOVNC_URL.sub(SITE, text)
        text = re.sub(r"\bnoVNC\b", TITLE, text)

        if text != original:
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.write(text)
            changed["text"] += 1
            print(f"[rebrand] text   {os.path.relpath(path, WWW)}")

print(f"[rebrand] summary: images={changed['icons']} text={changed['text']}")

# A rebrand that changed nothing is a failure, not a no-op.
if changed["icons"] == 0 and changed["text"] == 0:
    sys.exit("[rebrand] ERROR: nothing was replaced — check the web root")

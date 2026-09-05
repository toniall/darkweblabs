# Branding

Drop your artwork here and rebuild. All files are optional.

| File | Used for |
|---|---|
| `background.png` | XFCE wallpaper. 1920×1080 or larger. |
| `logo.svg` | Wide wordmark — the control bar, and inlined data URIs. |
| `icon.svg` | Square mark — the 13 PWA/favicon sizes. Falls back to `logo.svg`. |

    ./lab rebuild        # not `up` — Docker caches the COPY layer

Change the link and the page title without editing anything:

    LAB_BRAND_URL=https://example.org \
    LAB_BRAND_TITLE="My Lab" ./lab rebuild

## Why a script rather than a few `cp` commands

noVNC keeps its interface in a plain directory of files, so most of it is a
straight overwrite. Two parts are not:

1. **13 PNG icon sizes** under `app/images/icons`, each named for its own size,
   which have to be rasterised from `icon.svg` rather than copied.
2. **Text** — the page title in `vnc.html` and `index.html`, and the vendor
   product name and URL wherever they appear.

`rebrand.py` handles both, prints every file it modifies, and exits non-zero if
it replaced nothing. That last part matters: the previous build used KasmVNC,
whose marks were inlined into a bundle as base64 data URIs behind a symlinked
web root, and three rounds of replacing files reported success while leaving a
vendor logo on screen. A branding step that cannot fail loudly is worse than no
branding step.

## A note on trademarks

noVNC is MPL-2.0, so modifying it is fine. Replacing the project's marks
cleanly is legitimate, and safer than leaving them half-removed in a way that
might imply endorsement.

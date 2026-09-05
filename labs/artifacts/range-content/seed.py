#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Range content generator — Lab 8.1 / 8.5.

Generates the range's synthetic, watermarked content: a directory, a market, a
forum, a leak site, and a paste bin, plus a malicious clone of the market that
swaps only its PGP fingerprint and coin address. Everything is invented and every
page carries a visible synthetic-content banner — that watermark is a safety
control, not decoration, and the 8.1 check enforces it. Deterministic, so mirrors
are byte-identical and content hashes are stable. --selftest touches only a temp
dir it cleans up.
"""
import argparse
import hashlib
import os
import shutil
import sys
import tempfile

WATERMARK = ("SYNTHETIC — DARK WEB INTELLIGENCE LAB — NOT REAL — "
             "generated content, do not treat as live or trust any address/key here")

# genuine (market/mirror) vs clone-altered identity + payment material
GENUINE_PGP, GENUINE_BTC = "9A3F1C4D7E20BQ", "bc1q_market_k7"
CLONE_PGP,   CLONE_BTC   = "2E77A0B9C31DFP", "bc1q_clone_z9"


def _page(title, body):
    return (f"<!doctype html><html><head><meta charset=utf-8><title>{title}</title></head><body>"
            f"<div class=wm role=note>{WATERMARK}</div>"
            f"<h1>{title}</h1>{body}</body></html>\n")


def _directory():
    # deliberately partial + one stale entry; leak and paste are NOT listed
    items = [
        ("/market/", "Marketplace (synthetic)"),
        ("/market/", "Marketplace — mirror (synthetic)"),
        ("/forum/",  "Discussion forum (synthetic)"),
        ("/gone/",   "Old shop — MOVED (stale link)"),
    ]
    li = "".join(f'<li><a href="{u}">{lbl}</a></li>' for (u, lbl) in items)
    cross = ('<li>market i2p mirror: <code>synthetic.b32.i2p</code> (i2p)</li>'
             '<li>document archive: <code>USK@synthetic/archive/0/</code> (hyphanet)</li>')
    return _page("Range Directory",
                 f"<p>Known services (this list is incomplete on purpose):</p><ul>{li}</ul>"
                 f"<p>Cross-network references:</p><ul>{cross}</ul>")


def _market(pgp, btc):
    listings = "".join(
        f"<tr><td>item-{i:02d}</td><td>Synthetic Goods Co.</td><td>{(i*7) % 90 + 10} USD</td></tr>"
        for i in range(1, 9))
    return _page("Range Market",
                 f"<p>Vendor contact — PGP fingerprint: <code>{pgp}</code></p>"
                 f"<p>Payment address: <code>{btc}</code></p>"
                 f"<table><tr><th>listing</th><th>vendor</th><th>price</th></tr>{listings}</table>"
                 f"<p><a href='/login'>sign in</a> to see full catalogue.</p>")


def _forum():
    threads = "".join(f"<li>Thread {i}: synthetic discussion #{i}</li>" for i in range(1, 6))
    return _page("Range Forum",
                 f"<ul>{threads}</ul><p>PGP-signed posts (synthetic keys) below the fold. "
                 f"<a href='/login'>sign in</a> to read member boards.</p>")


def _leak():
    victims = "".join(f"<li>VICTIM-{i} Holdings (invented) — countdown 0{i}:00:00 — "
                      f"<a href='/proof/{i}'>proof archive</a> (empty, watermarked)</li>"
                      for i in range(1, 4))
    return _page("Range Leak Site",
                 f"<p>This is a synthetic extortion-page model. No real breach data exists here.</p>"
                 f"<ul>{victims}</ul>")


def _paste():
    return _page("Range Paste", "<pre>synthetic paste content — no real secrets — watermarked</pre>")


def _services():
    """Return {name: html}. Mirror serves the market's exact bytes."""
    market = _market(GENUINE_PGP, GENUINE_BTC)
    return {
        "directory":     _directory(),
        "market":        market,
        "market-mirror": market,                       # byte-identical -> mirror
        "market-clone":  _market(CLONE_PGP, CLONE_BTC),  # altered pgp+btc -> clone
        "forum":         _forum(),
        "leak":          _leak(),
        "paste":         _paste(),
    }


def generate(outdir):
    svcs = _services()
    hashes = {}
    for name, html in svcs.items():
        d = os.path.join(outdir, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w") as fh:
            fh.write(html)
        hashes[name] = hashlib.sha256(html.encode()).hexdigest()[:16]
    return hashes


def selftest():
    ok = True
    tmp = tempfile.mkdtemp(prefix="range-seed-")
    try:
        h1 = generate(tmp)
        # 1) every generated page carries the watermark
        for root, _, files in os.walk(tmp):
            for f in files:
                if f.endswith(".html") and WATERMARK not in open(os.path.join(root, f)).read():
                    ok = False
        svcs = _services()
        # 2) mirror is byte-identical to the market
        if h1["market"] != h1["market-mirror"] or svcs["market"] != svcs["market-mirror"]:
            ok = False
        # 3) clone differs from the market...
        if svcs["market-clone"] == svcs["market"] or h1["market-clone"] == h1["market"]:
            ok = False
        # 4) ...and ONLY in the swapped pgp + btc fields
        restored = svcs["market-clone"].replace(CLONE_PGP, GENUINE_PGP).replace(CLONE_BTC, GENUINE_BTC)
        if restored != svcs["market"]:
            ok = False
        # 5) deterministic: a second generation yields identical hashes
        tmp2 = tempfile.mkdtemp(prefix="range-seed2-")
        try:
            if generate(tmp2) != h1:
                ok = False
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("selftest: every page is watermarked, the mirror is byte-identical, and the")
    print(f"          clone differs from the market only in its swapped pgp+btc"
          f"  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", help="generate the range content into this directory")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.out:
        ap.error("give --out <dir> to generate content, or --selftest")
    hs = generate(a.out)
    print(f"generated {len(hs)} services into {a.out}")
    for k, v in hs.items():
        print(f"  {k:14} sha256:{v}")

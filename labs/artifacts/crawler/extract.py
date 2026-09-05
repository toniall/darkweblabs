#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Link + content extraction — Chapter 9 (Labs 9.3, 9.6).

Dark-web pages link both with <a href> and as bare addresses dropped in text, so
extraction has to catch both, classify each by network, and pull the key material
(PGP fingerprint, coin address) that later tells a clone from the real service.
content_hash ignores nothing but the bytes, so a mirror (same content, different
onion) hashes identically to its origin. Pure functions; --selftest runs on the
bundled fixture pages.
"""
import argparse
import hashlib
import re
import sys

from frontier import classify_network, normalize_url

_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
# bare addresses in text: onion v3, i2p, or a Hyphanet key
_BARE_RE = re.compile(
    r'(?:[a-z2-7]{56}\.onion(?:/[^\s<>"\']*)?'
    r'|[a-z2-7]{52}\.b32\.i2p(?:/[^\s<>"\']*)?'
    r'|\b(?:USK|SSK|CHK|KSK)@[^\s<>"\']+)', re.I)
_PGP_RE = re.compile(r'\b([0-9A-Z]{14,40})\b')
_BTC_RE = re.compile(r'\b(bc1q[a-z0-9_]+)\b')


def extract_links(html, base=None):
    """Return a de-duplicated list of (address, network) from href and bare text.

    hrefs may be relative and are resolved against base; bare dark-web addresses
    in text are absolute identifiers and must NOT be joined to base (doing so would
    mangle an off-network address into a path under the current host)."""
    found = []
    seen = set()

    def _add(addr):
        net = classify_network(addr)
        key = (addr, net)
        if key not in seen:
            seen.add(key)
            found.append(key)

    for raw in _HREF_RE.findall(html):          # relative or absolute -> resolve
        _add(normalize_url(raw, base))
    for raw in _BARE_RE.findall(html):          # absolute identifier -> never join
        if "@" in raw:                          # a Hyphanet key, not a URL
            _add(raw)
        else:                                   # onion / i2p host -> give it a scheme
            _add(normalize_url("http://" + raw))
    return found


def extract_keys(html):
    """Pull the identity/payment material a page advertises (for clone detection)."""
    pgp = _PGP_RE.search(html)
    btc = _BTC_RE.search(html)
    return {"pgp": pgp.group(1) if pgp else None,
            "btc": btc.group(1) if btc else None}


def content_hash(html):
    """Stable hash of the page bytes — identical content hashes identically,
    which is what lets a mirror be recognised as the same service."""
    return hashlib.sha256(html.encode()).hexdigest()[:16]


_FIXTURE = (
    "<html><body><div class=wm>SYNTHETIC</div>"
    "<a href='/listings'>catalogue</a>"
    "<p>vendor pgp 9A3F1C4D7E20BQ pays to bc1q_market_k7</p>"
    "<p>mirror at " + "c" * 56 + ".onion and archive USK@cafe/docs/0/</p>"
    "<p>eepsite " + "d" * 52 + ".b32.i2p</p></body></html>")


def selftest():
    ok = True
    base = "http://" + "a" * 56 + ".onion/"
    links = extract_links(_FIXTURE, base)
    nets = {net for _, net in links}
    # href resolves to a tor path; bare onion, i2p, and hyphanet all classified
    if not ({"tor", "i2p", "hyphanet"} <= nets):
        print(f"  networks found: {nets}")
        ok = False
    if not any(a.endswith("/listings") for a, _ in links):
        ok = False

    keys = extract_keys(_FIXTURE)
    if keys["pgp"] != "9A3F1C4D7E20BQ" or keys["btc"] != "bc1q_market_k7":
        print(f"  keys: {keys}")
        ok = False

    # identical content hashes identically; a changed byte changes the hash
    if content_hash(_FIXTURE) != content_hash(_FIXTURE):
        ok = False
    if content_hash(_FIXTURE) == content_hash(_FIXTURE + " "):
        ok = False

    print("selftest: href + bare-text links are extracted and classified, key material")
    print(f"          is pulled, and content hashing is stable  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    ap.error("use --selftest")

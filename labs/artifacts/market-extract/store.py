#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Content-addressed page store — Chapter 11 (Lab 11.1).

Chapter 10 could only run on a shipped corpus because the Chapter 9 crawler kept
addresses and keys, not page bodies. This is the store that closes that gap. Every
fetched body is written under the hash of its own content, so a byte-identical mirror
fetched from two addresses is stored once — the same collapse Chapter 10 does at
detection time, done here at storage time. Provenance (which address served which
object, and when) is recorded separately, so the store answers both "what did the
page say" and "where and when did we see it." Extraction then runs offline over the
store, re-runnably, and the store can export its bodies for the Chapter 10 detector
to cluster — the whole pipeline on one set of real pages. The digest is the Chapter 9
content hash, so the store and the mirror detector agree on identity.
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "crawler"))
from extract import content_hash   # noqa: E402  (reuse Ch9's identity hash)


def _paths(store_dir):
    return os.path.join(store_dir, "objects"), os.path.join(store_dir, "provenance.jsonl")


def put(store_dir, url, body, fetched_at="2026-07-30T00:00:00Z"):
    """Store a page body under its content hash; record where/when it was seen.
    Returns the digest. Byte-identical bodies share one object (content addressing)."""
    objects, prov = _paths(store_dir)
    os.makedirs(objects, exist_ok=True)
    digest = content_hash(body)
    obj = os.path.join(objects, digest + ".html")
    if not os.path.exists(obj):                 # identical body already stored -> skip
        with open(obj, "w") as fh:
            fh.write(body)
    with open(prov, "a") as fh:
        fh.write(json.dumps({"url": url, "digest": digest,
                             "fetched_at": fetched_at, "bytes": len(body)}) + "\n")
    return digest


def get(store_dir, digest):
    objects, _ = _paths(store_dir)
    with open(os.path.join(objects, digest + ".html")) as fh:
        return fh.read()


def provenance(store_dir):
    """Every fetch event: url, digest, fetched_at, bytes (mirrors share a digest)."""
    _, prov = _paths(store_dir)
    if not os.path.exists(prov):
        return []
    return [json.loads(line) for line in open(prov) if line.strip()]


def objects(store_dir):
    """The set of distinct stored object digests."""
    obj_dir, _ = _paths(store_dir)
    if not os.path.isdir(obj_dir):
        return []
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(obj_dir, "*.html")))


def export_bodies(store_dir, out_dir):
    """Write each distinct object as an HTML file, so the Chapter 10 detector can
    cluster real collected bodies (./lab dedup run --dir <out_dir>)."""
    os.makedirs(out_dir, exist_ok=True)
    # name each object by the last address that served it, for readability
    last_url = {}
    for ev in provenance(store_dir):
        last_url[ev["digest"]] = ev["url"]
    n = 0
    for dg in objects(store_dir):
        slug = last_url.get(dg, dg).rstrip("/").rsplit("/", 1)[-1] or dg
        with open(os.path.join(out_dir, f"{slug}.html"), "w") as fh:
            fh.write(get(store_dir, dg))
        n += 1
    return n


def ingest_dir(store_dir, corpus_dir):
    """Populate the store from a directory of pages, as if crawled — each file's name
    stands in for the address it was served from."""
    for p in sorted(glob.glob(os.path.join(corpus_dir, "*.html"))):
        name = os.path.basename(p)
        put(store_dir, url=f"http://market.example/{name}", body=open(p).read())


def selftest():
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        store = os.path.join(d, "store")
        body = "<html><body>listing 1001</body></html>"
        mirror = body                             # byte-identical mirror
        other = "<html><body>listing 1002</body></html>"

        d1 = put(store, "http://a.onion/1001", body)
        d2 = put(store, "http://b.onion/1001", mirror)   # same content, different address
        d3 = put(store, "http://a.onion/1002", other)

        # content addressing: the mirror collapsed to one object; two distinct bodies
        if not (d1 == d2 and d1 != d3 and len(objects(store)) == 2):
            print(f"  objects={len(objects(store))} d1==d2:{d1==d2}")
            ok = False
        # provenance kept all three fetch events, two of them pointing at the shared object
        prov = provenance(store)
        if not (len(prov) == 3 and sum(1 for e in prov if e["digest"] == d1) == 2):
            ok = False
        # bodies round-trip
        if get(store, d1) != body:
            ok = False
        # re-storing is idempotent (re-runnable collection doesn't duplicate objects)
        put(store, "http://a.onion/1001", body)
        if len(objects(store)) != 2:
            ok = False
        # export produces one file per distinct object, for the Ch10 detector
        out = os.path.join(d, "bodies")
        if export_bodies(store, out) != 2:
            ok = False

    print("selftest: byte-identical mirrors collapse to one stored object, provenance keeps")
    print(f"          every sighting, and the store exports bodies for dedup  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ingest", metavar="DIR")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.ingest:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            st = os.path.join(d, "store")
            bodies = os.path.join(d, "bodies")
            ingest_dir(st, a.ingest)
            prov, objs = provenance(st), objects(st)
            n = export_bodies(st, bodies)
            print(f"  ingested {len(prov)} fetched pages -> {len(objs)} distinct objects")
            print(f"  {len(prov) - len(objs)} byte-identical mirror collapsed at storage "
                  "(content addressing = Ch10 exact-mirror, at storage time)")
            print(f"  provenance kept every sighting; exported {n} bodies "
                  "for: ./lab dedup run --dir <store>/bodies")
        sys.exit(0)
    ap.error("use --selftest or --ingest DIR")

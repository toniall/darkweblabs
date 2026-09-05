#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Clustering look-alikes into sites — Chapter 10 (Labs 10.5, 10.6, 10.7).

Every earlier lab compares two pages; this one turns those pairwise judgments into
sites. An edge joins two pages when they are near-duplicates by text (shingling) or
share a template AND at least one asset file (structure + signals) — the second
clause is what admits a reworded, keyless clone while keeping a different service on
the same template out. Union-find collapses the edges into clusters, each cluster a
single operator's footprint; within a cluster the canonical is the directory-listed
address and every other member is classed a mirror (same operator) or a clone
(impersonation). The engine is parameterised: naive mode is the Chapter 9 detector
(exact-hash mirrors, keyed-structural clones); full mode is everything here. Its
--selftest runs the dedup scorer on its own output, naive vs full.
"""
import argparse
import glob
import json
import os
import sys

import shingle
import signals
import structure
from signals import content_hash, intent, keymask_hash, keys

S_HIGH = 0.5    # shingle Jaccard at/above this -> near-duplicate by text
T_HIGH = 0.85   # structure SimHash at/above this -> same template


class _UF:
    def __init__(self, items):
        self.p = {x: x for x in items}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb

    def groups(self):
        g = {}
        for x in self.p:
            g.setdefault(self.find(x), []).append(x)
        return [sorted(v) for v in g.values()]


def _edge_full(pages, a, b):
    if shingle.text_similarity(pages[a], pages[b]) >= S_HIGH:
        return True
    if (structure.structure_sim(pages[a], pages[b]) >= T_HIGH
            and signals.shared_assets(pages[a], pages[b])):
        return True
    return False


def _pick_canonical(members, directory):
    listed = [m for m in members if m in directory]
    if listed:
        return sorted(listed)[0]
    keyed = [m for m in members if keys(pages_ref[m]).get("btc")]
    return sorted(keyed)[0] if keyed else sorted(members)[0]


pages_ref = {}   # set by cluster() so _pick_canonical can read page content


def cluster(pages, directory=None, full=True):
    global pages_ref
    pages_ref = pages
    directory = set(directory or [])
    names = sorted(pages)

    uf = _UF(names)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if full:
                joined = _edge_full(pages, a, b)
            else:
                joined = content_hash(pages[a]) == content_hash(pages[b])   # exact only
            if joined:
                uf.union(a, b)

    groups = uf.groups()

    # naive mode also runs the Chapter 9 keyed-structural clone check: a page whose
    # key-masked hash matches a directory canonical but whose keys differ is a clone
    if not full:
        canon_by_mask = {}
        for g in groups:
            canon = _pick_canonical(g, directory)
            if canon in directory:
                canon_by_mask.setdefault(keymask_hash(pages[canon]), canon)
        root = {m: uf.find(m) for m in names}
        for g in list(groups):
            if len(g) == 1:
                p = g[0]
                if p in directory:
                    continue
                mh = keymask_hash(pages[p])
                canon = canon_by_mask.get(mh)
                if canon and keys(pages[p]) != keys(pages[canon]) and keys(pages[p]).get("btc"):
                    uf.union(p, canon)
        groups = uf.groups()

    clusters = []
    for g in groups:
        canon = _pick_canonical(g, directory)
        members = [{"address": canon, "role": "canonical"}]
        for m in sorted(x for x in g if x != canon):
            ts = shingle.text_similarity(pages[canon], pages[m])
            role, reason = intent(pages[canon], pages[m], m in directory, ts)
            members.append({"address": m, "role": role, "reason": reason})
        clusters.append({"canonical": canon, "members": members})
    clusters.sort(key=lambda c: c["canonical"])
    return {"clusters": clusters}


def _load_dir(path):
    pages = {os.path.basename(p): open(p).read()
             for p in glob.glob(os.path.join(path, "*.html"))}
    # convention for the clone-lab corpus: originals are the pages the directory lists,
    # i.e. those not named as a mirror or a clone
    directory = {n for n in pages if "mirror" not in n and "clone" not in n}
    return pages, directory


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    pages, directory = _load_dir(os.path.join(here, "corpus"))
    sys.path.insert(0, os.path.join(here, "..", "dedup-scorer"))
    import scorer

    truth = json.load(open(os.path.join(here, "..", "dedup-scorer", "manifest.json")))
    naive = scorer.score(truth, cluster(pages, directory, full=False))
    full = scorer.score(truth, cluster(pages, directory, full=True))

    ok = True
    # naive (Chapter 9 detector): only the exact mirror groups, only the keyed clone caught
    if not (naive["mirror_recall"] == 0.33 and naive["clone_recall"] == 0.5
            and naive["false_merges"] == 0):
        ok = False
    # full engine: every mirror grouped, both clones caught, precision clean, no false merge
    if not (full["mirror_recall"] == 1.0 and full["clone_recall"] == 1.0
            and full["clone_precision"] == 1.0 and full["false_merges"] == 0):
        ok = False
    # strict improvement where it counts, and the trap stays separate in both
    if not (full["mirror_recall"] > naive["mirror_recall"]
            and full["clone_recall"] > naive["clone_recall"]):
        ok = False

    print(f"selftest: naive groups mirror {naive['mirror_recall']:.2f}, clone {naive['clone_recall']:.2f};")
    print(f"          full groups mirror {full['mirror_recall']:.2f}, clone {full['clone_recall']:.2f}, "
          f"no false merge  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", help="a directory of .html pages to cluster")
    ap.add_argument("--naive", action="store_true", help="exact-hash + keyed-structural only")
    ap.add_argument("--out", help="write the dedup-output JSON here")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.dir:
        pages, directory = _load_dir(a.dir)
        out = cluster(pages, directory, full=not a.naive)
        text = json.dumps(out, indent=2)
        if a.out:
            open(a.out, "w").write(text)
            print(f"wrote {a.out}: {len(out['clusters'])} clusters "
                  f"({'naive' if a.naive else 'full engine'})")
        else:
            print(text)
    else:
        ap.error("use --selftest, or --dir <corpus> [--naive] [--out file]")

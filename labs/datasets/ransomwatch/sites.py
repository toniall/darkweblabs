#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Chapter 12 leak-site channel on real data: run the leak-site analysis over the
ransomwatch feed (leaksite.db). Victim extraction, per-group lifecycle, reposts,
and cross-group listings are all real here — including the re-extortion pattern
where one victim is posted by one group and then another.

Deterministic. Usage:  python3 sites.py [--db leaksite.db] [--json] | --selftest
"""
import sqlite3, os, sys, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "leaksite.db")


def snapshot_line(db_path):
    """Data-provenance banner: source, capture date, and how current the feed is.
    These come from the bundled snapshot; ./lab update re-fetches and re-stamps them."""
    try:
        c = sqlite3.connect(db_path)
        st = {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
        c.close()
    except Exception:
        st = {}
    src = (st.get("source", "") or "").rstrip("/").replace("https://github.com/", "").replace(".git", "") or "bundled snapshot"
    cap = st.get("captured_at", "unknown")
    through = st.get("date_max")
    tail = ", posts through %s" % through if through else ""
    return "  data snapshot     %s \u00b7 captured %s%s  (run ./lab update to refresh)" % (src, cap, tail)


def analyze(db_path):
    c = sqlite3.connect(db_path).cursor()

    # victim extraction + lifecycle per group
    groups = []
    for name, n_posts, n_victims, first, last, active in c.execute(
            "SELECT name, n_posts, n_victims, first_seen, last_seen, active_days FROM groups ORDER BY n_posts DESC"):
        groups.append({"group": name, "posts": n_posts, "victims": n_victims,
                       "first": first, "last": last, "active_days": active})

    # reposts: a victim posted more than once
    reposts = c.execute("""SELECT victim_id, COUNT(*) n FROM posts GROUP BY victim_id
                           HAVING n > 1 ORDER BY n DESC""").fetchall()

    # cross-group: a victim on two or more groups' sites (re-victimization)
    cross = c.execute("""SELECT victim_id, COUNT(DISTINCT group_name) g FROM posts
                         GROUP BY victim_id HAVING g > 1 ORDER BY g DESC""").fetchall()
    example = None
    if cross:
        vid = cross[0][0]
        hits = c.execute("SELECT group_name, ymd FROM posts WHERE victim_id=? ORDER BY ordinal", (vid,)).fetchall()
        example = {"victim": vid, "hits": hits}

    longest = max(groups, key=lambda g: g["active_days"]) if groups else None
    most = groups[0] if groups else None
    return {
        "n_groups": len(groups), "n_victims": sum(g["victims"] for g in groups),
        "most_prolific": most, "longest_running": longest,
        "n_reposts": len(reposts), "top_repost": reposts[0] if reposts else None,
        "n_crossgroup": len(cross), "example": example,
        "top_groups": groups[:6], "_snapshot": snapshot_line(db_path),
    }


def render(r):
    L = ["Chapter 12 leak-site channel over the real ransomwatch feed", ""]
    if r.get("_snapshot"):
        L += [r["_snapshot"], ""]
    L.append(f'  extracted         {r["n_victims"]} victims across {r["n_groups"]} groups')
    if r["most_prolific"]:
        m = r["most_prolific"]
        L.append(f'  most prolific     {m["group"]}  ({m["victims"]} victims)')
    if r["longest_running"]:
        lr = r["longest_running"]
        L.append(f'  longest running   {lr["group"]}  ({lr["active_days"]} days, {lr["first"]} to {lr["last"]})')
    L.append("")
    L.append("  lifecycle, most active groups:")
    for g in r["top_groups"]:
        L.append(f'    {g["group"]:16} {g["victims"]:4} victims  {g["first"]} to {g["last"]}')
    L.append("")
    L.append(f'  reposts           {r["n_reposts"]} victims posted more than once')
    if r["top_repost"]:
        L.append(f'    most reposted: {r["top_repost"][0]} x{r["top_repost"][1]}')
    L.append(f'  cross-group       {r["n_crossgroup"]} victims listed by two or more groups (re-extortion)')
    if r["example"]:
        L.append("    example (the bluff that deletion was final):")
        for g, ymd in r["example"]["hits"]:
            L.append(f'      {r["example"]["victim"]}  {g:16} {ymd}')
    return "\n".join(L)


def selftest():
    r = analyze(DB)
    ok = (r["n_groups"] >= 50 and r["n_victims"] >= 5000
          and r["n_reposts"] >= 1 and r["n_crossgroup"] >= 1
          and r["example"] is not None and len(r["example"]["hits"]) >= 2
          and r["longest_running"] is not None)
    print(render(r)); print(); print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    db = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else DB
    r = analyze(db)
    print(json.dumps(r, indent=2) if "--json" in sys.argv else render(r))

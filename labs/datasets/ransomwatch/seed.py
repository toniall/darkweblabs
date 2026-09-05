#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Build leaksite.db from the ransomwatch corpus of real ransomware leak-site posts.

Feeds two chapters, offline:
  - Chapter 14 (monitoring): the time-ordered post stream is a real change-feed —
    new victims genuinely appear over time, which is what the detector consumes.
  - Chapter 12 (leak-site channel): reposts (a victim posted more than once) and
    cross-group listings (the same victim on two groups' sites) are real here.

The DB is COMMITTED pre-built, so a reader never fetches anything. Victim names
are the one piece of PII: each real company name is replaced by a stable salted
pseudonym (victim-XXXXXX), so reposts and cross-group listings stay detectable
(same company -> same pseudonym) while no real victim is ever named. Group names
are the operators and are kept, as in the Casualtek corpus.

Usage:
  python3 seed.py [--src DIR] [--out leaksite.db] [--selftest]

Source: https://github.com/joshhighet/ransomwatch  (MIT; aggregated public
leak-site metadata). With --src, reads DIR/posts.json; without it, shallow-clones.
"""
import sqlite3, json, re, sys, os, hashlib, subprocess, tempfile, statistics
from datetime import datetime
from collections import Counter, defaultdict

REPO = "https://github.com/joshhighet/ransomwatch.git"
SALT = "darkweblabs-ransomwatch-v1"          # fixed -> reproducible pseudonyms


def pseudonym(name):
    h = hashlib.sha256((SALT + "|" + name.strip().lower()).encode()).hexdigest()
    return "victim-" + h[:6]


def norm_group(g):
    return re.sub(r"[^a-z0-9]+", "", (g or "").strip().lower()) or "unknown"


def parse_day(ts):
    ts = (ts or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts[:26], fmt).date()
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", ts)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3])).date()
    return None


def load(src):
    path = os.path.join(src, "posts.json")
    return json.load(open(path, encoding="utf-8"))


def build(src, out):
    if os.path.exists(out):
        os.remove(out)
    rows = load(src)
    db = sqlite3.connect(out)
    c = db.cursor()
    c.executescript("""
      CREATE TABLE posts(
        seq INTEGER PRIMARY KEY, group_name TEXT, victim_id TEXT,
        ymd TEXT, ordinal INTEGER);
      CREATE TABLE groups(
        name TEXT PRIMARY KEY, n_posts INT, n_victims INT,
        first_seen TEXT, last_seen TEXT, active_days INT);
      CREATE TABLE stats(key TEXT PRIMARY KEY, value TEXT);
      CREATE INDEX ix_posts_ord ON posts(ordinal);
      CREATE INDEX ix_posts_grp ON posts(group_name);
      CREATE INDEX ix_posts_vic ON posts(victim_id);
    """)

    recs = []
    for r in rows:
        d = parse_day(r.get("discovered"))
        title = (r.get("post_title") or "").strip()
        if not d or not title:
            continue
        recs.append((norm_group(r.get("group_name")), pseudonym(title), d))
    recs.sort(key=lambda x: x[2])                      # chronological = the feed
    base = recs[0][2]
    for seq, (g, vid, d) in enumerate(recs):
        c.execute("INSERT INTO posts VALUES(?,?,?,?,?)",
                  (seq, g, vid, d.isoformat(), (d - base).days))

    # per-group aggregate
    by_g = defaultdict(list)
    for g, vid, d in recs:
        by_g[g].append((vid, d))
    for g, items in by_g.items():
        days = [d for _, d in items]
        c.execute("INSERT INTO groups VALUES(?,?,?,?,?,?)",
                  (g, len(items), len({v for v, _ in items}),
                   min(days).isoformat(), max(days).isoformat(),
                   (max(days) - min(days)).days + 1))

    # derived distributions for the calibrated-synthetic upgrade
    victim_groups = defaultdict(set)
    victim_count = Counter()
    for g, vid, _ in recs:
        victim_groups[vid].add(g)
        victim_count[vid] += 1
    reposts = sum(1 for v, n in victim_count.items() if n > 1)
    crossgroup = sum(1 for v, gs in victim_groups.items() if len(gs) > 1)
    span_days = (recs[-1][2] - recs[0][2]).days + 1
    posts_per_month = Counter(d.strftime("%Y-%m") for _, _, d in recs)
    stats = {
        "n_posts": len(recs),
        "n_groups": len(by_g),
        "n_victims": len(victim_count),
        "date_min": recs[0][2].isoformat(),
        "date_max": recs[-1][2].isoformat(),
        "span_days": span_days,
        "posts_per_day_mean": round(len(recs) / span_days, 3),
        "repost_victims": reposts,
        "repost_rate": round(reposts / len(victim_count), 4),
        "crossgroup_victims": crossgroup,
        "crossgroup_rate": round(crossgroup / len(victim_count), 4),
        "median_posts_per_month": int(statistics.median(posts_per_month.values())),
        "top_groups": [g for g, _ in Counter(
            {g: len(v) for g, v in by_g.items()}).most_common(10)],
    }
    for k, v in stats.items():
        c.execute("INSERT INTO stats VALUES(?,?)", (k, json.dumps(v)))
    # provenance + freshness stamp (read by the labs, the report, and the book note):
    # captured_at = the day this snapshot was built; date_max above = newest post in it.
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)",
              ("captured_at", json.dumps(datetime.now().date().isoformat())))
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("source", json.dumps(REPO)))
    try:
        sha = subprocess.check_output(["git", "-C", src, "rev-parse", "--short", "HEAD"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        c.execute("INSERT OR REPLACE INTO stats VALUES(?,?)", ("source_commit", json.dumps(sha)))
    except Exception:
        pass
    db.commit()
    return db


def clone_to_temp():
    d = tempfile.mkdtemp(prefix="ransomwatch-")
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", REPO, d], check=True)
    return d


def selftest(out):
    db = sqlite3.connect(out)
    c = db.cursor()
    np = c.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    ng = c.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    # no raw victim names: every victim_id must be a pseudonym
    bad = c.execute("SELECT COUNT(*) FROM posts WHERE victim_id NOT LIKE 'victim-%'").fetchone()[0]
    # the feed is monotonic in ordinal
    mono = c.execute("SELECT MIN(ordinal), MAX(ordinal) FROM posts").fetchone()
    reposts = json.loads(c.execute("SELECT value FROM stats WHERE key='repost_victims'").fetchone()[0])
    cross = json.loads(c.execute("SELECT value FROM stats WHERE key='crossgroup_victims'").fetchone()[0])
    ok = np >= 5000 and ng >= 50 and bad == 0 and mono[0] == 0 and reposts > 0 and cross > 0
    print(f"posts={np} groups={ng} pseudonym-leaks={bad} reposts={reposts} cross-group={cross}")
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    here = os.path.dirname(os.path.abspath(__file__))
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(here, "leaksite.db")
    if "--selftest" in args and "--src" not in args:
        sys.exit(selftest(out))
    src = args[args.index("--src") + 1] if "--src" in args else None
    cleanup = False
    if not src:
        print("cloning ransomwatch ..."); src = clone_to_temp(); cleanup = True
    print(f"building {out} from {src} ...")
    build(src, out)
    if cleanup:
        subprocess.run(["rm", "-rf", src])
    sys.exit(selftest(out))

#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""
Refresh the real-data snapshots from their public GitHub sources and rebuild the
committed databases in place, re-stamping the capture date.

The results printed in the book (Chapters 11, 12, 14 real-data labs) and drawn in
the intel report come from the snapshot BUNDLED in this repo. Run this to pull the
current data instead; wherever the upstream feed has moved on, the labs' numbers
and the report's "data as of" date will change. Re-run the labs afterwards to see
the new picture, then compare against what the book prints.

Only the ransomwatch leak-site feed is live-updating. The Agora market and the
Casualtek negotiation corpus are fixed historical archives, so this refreshes
ransomwatch by default; pass --all to re-fetch the archives too (same data, new
capture date).

Usage:  python3 update.py            # refresh the ransomwatch feed
        python3 update.py --all      # also re-fetch the static archives
"""
import sqlite3, json, os, sys, subprocess
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RW_SEED = os.path.join(HERE, "ransomwatch", "seed.py")
RW_DB   = os.path.join(HERE, "ransomwatch", "leaksite.db")


def stats(db):
    if not os.path.exists(db):
        return {}
    c = sqlite3.connect(db)
    try:
        return {k: json.loads(v) for k, v in c.execute("SELECT key, value FROM stats")}
    except Exception:
        return {}
    finally:
        c.close()


def refresh_ransomwatch():
    before = stats(RW_DB)
    print("\u25b8 ransomwatch  (source: %s)" % before.get("source", "github.com/joshhighet/ransomwatch"))
    print("  before : %s posts, through %s, snapshot %s"
          % (before.get("n_posts", "?"), before.get("date_max", "?"), before.get("captured_at", "?")))
    tmp = RW_DB + ".new"
    print("  fetching the current feed from GitHub ...")
    r = subprocess.run([sys.executable, RW_SEED, "--out", tmp], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        print("  ! fetch failed \u2014 keeping the existing snapshot.\n    " + (r.stderr or r.stdout).strip()[-300:])
        return False
    after = stats(tmp)
    if int(after.get("n_posts", 0)) == 0:
        os.remove(tmp)
        print("  ! feed returned no posts \u2014 keeping the existing snapshot.")
        return False
    os.replace(tmp, RW_DB)   # atomic swap only after a good build
    dposts = int(after.get("n_posts", 0)) - int(before.get("n_posts", 0))
    dgroups = int(after.get("n_groups", 0)) - int(before.get("n_groups", 0))
    print("  after  : %s posts, through %s, snapshot %s"
          % (after.get("n_posts", "?"), after.get("date_max", "?"), after.get("captured_at", "?")))
    print("  change : %+d posts, %+d groups" % (dposts, dgroups))
    if dposts == 0 and before.get("date_max") == after.get("date_max"):
        print("  = upstream feed has not advanced since the bundled snapshot; capture date re-stamped to %s."
              % after.get("captured_at"))
    else:
        print("  \u2713 leaksite.db refreshed. Re-run  ./lab leak realsite  and  ./lab detect realfeed  \u2014 the numbers will differ from the book.")
    return True


def refresh_archives():
    for name, seed, db in [
        ("agora market", os.path.join(HERE, "agora", "seed.py"), os.path.join(HERE, "agora", "market.db")),
        ("casualtek corpus", os.path.join(HERE, "..", "artifacts", "ransomchat", "seed.py"),
         os.path.join(HERE, "..", "artifacts", "ransomchat", "negotiations.db")),
    ]:
        print("\u25b8 %s  (fixed historical archive)" % name)
        tmp = db + ".new"
        r = subprocess.run([sys.executable, seed, "--out", tmp], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            os.replace(tmp, db)
            print("  \u2713 re-fetched; capture date re-stamped (data is unchanged \u2014 dead/archived source).")
        else:
            if os.path.exists(tmp):
                os.remove(tmp)
            print("  ! re-fetch skipped/failed \u2014 kept existing.")


def main():
    print("Refreshing real-data snapshots from public GitHub sources ...\n")
    refresh_ransomwatch()
    if "--all" in sys.argv:
        print()
        refresh_archives()
    print("\nDone. The book's printed results reflect the bundled snapshot; your databases now reflect what you just fetched.")


if __name__ == "__main__":
    main()

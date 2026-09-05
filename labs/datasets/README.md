# Offline real-data corpora

This folder holds **real, public datasets** turned into small, scrubbed, offline
SQLite databases that ground several chapters in genuine data instead of a purely
synthetic range. Everything ships **pre-built and committed** — a reader never
fetches anything, and the labs run fully offline.

It follows the pattern proven by Chapter 12's RansomChat: a `seed.py` clones a
public source, scrubs residual PII, and builds a `*.db`; the built DB is
committed, so the seeder is for reproducibility only.

## Design rules (the same ones the book holds elsewhere)

- **Graded core stays synthetic and deterministic.** These real corpora feed
  *optional, ungraded* labs and *calibrate* the synthetic generators (real
  distributions), so the graded checks keep asserting fixed numbers.
- **Never name a real person or company.** Victim and vendor names are replaced
  with stable salted pseudonyms (`victim-XXXXXX`, `vendor-XXXX`). The pseudonym
  is consistent, so structure survives — reposts, cross-group listings, and
  vendor graphs still resolve — but no real entity is named.
- **Operators are kept.** Ransomware group names are the operators, treated the
  same as in the Casualtek corpus.
- **No operational free-text.** Market listing descriptions (which describe
  illegal goods) are reduced to category/price/feedback structure; the raw text
  is dropped.

## What's here

### `ransomwatch/` — real ransomware leak-site posts
- Source: https://github.com/joshhighet/ransomwatch (MIT; aggregated public
  leak-site metadata).
- `seed.py` builds `leaksite.db`: **16,072 posts, 157 groups, 2020-2025**.
  Tables: `posts(seq, group_name, victim_id, ymd, ordinal)`,
  `groups(...aggregate...)`, `stats(...derived distributions...)`.
- Feeds **Chapter 14** (the time-ordered stream is a real change-feed — new
  victims genuinely appear over time) and the **Chapter 12 leak-site channel**
  (reposts and cross-group listings are real: e.g. a victim posted by one group
  and reposted by another days later).
- Rebuild: `python3 seed.py --src /path/to/ransomwatch` (or no `--src` to clone).
  Self-check: `python3 seed.py --selftest`.

### `agora/` — real darknet-market listings  *(pending source decision)*
- Candidate source: a public Agora-market dataset (market dead since 2015).
- Intended to feed **Chapter 11** (calibrated-synthetic market from real price /
  vendor-concentration / feedback / shipping-lane distributions, plus an optional
  real-slice extraction lab).

## Reproducibility

Pseudonyms use a fixed salt committed in each `seed.py`, so rebuilding produces
identical IDs. The committed `*.db` is the source of truth for the labs.

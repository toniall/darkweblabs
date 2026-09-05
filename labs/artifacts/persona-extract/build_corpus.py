#!/usr/bin/env python3
# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
"""Builds the persona-lab corpus — pseudonyms across markets, leak sites, and forums, for Chapter 13.

Attribution links pseudonyms into operators, and this corpus is built so every kind of
link and every kind of trap has ground truth. One operator (Alpha) appears as a market
vendor, two leak-site brands, and a forum handle, tied by a reused signed key and wallet
(the Chapter 12 operator tell), a consistent writing voice, a shared activity rhythm, a
handle transformation, and a repeated tactic sequence — a hard link with soft
corroboration. A second operator (Bravo) rotated both key and wallet across a market
vendor and a leak brand, so ONLY the soft signals — voice and rhythm — re-link them: the
false negative the soft stack must recover. A third (Charlie, the Chapter 11 borrowed-key
vendor) DISPLAYS Alpha's key but signs with its own and writes in a different voice: the
false positive a naive linker merges and provenance must reject. A fourth (Delta) is a
forum look-alike whose handle resembles Alpha's but shares no key, wallet, voice, or
rhythm: the handle-only trap. Every profile is watermarked synthetic — invented handles,
fake keys and wallets, placeholder text. Nothing here links to a real person. Run once to
(re)generate corpus/.
"""
import os

WM = "=== SYNTHETIC LAB DATA — persona profile ==="

# --- reused identifiers, echoing Chapters 11 and 12 ---
K_ALPHA = "F19B7A0C4E82D5613FA0"                       # Ch12 operator tell, reused across Alpha's personas
W_ALPHA = "bc1qsynth0laba0000000000000000000000zzzz"   # Ch12 wallet
K_BRAVO1 = "A1B2C3D4E5F60718293A"; W_BRAVO1 = "bc1qsynth0bravo1000000000000000000000wwww"
K_BRAVO2 = "0F1E2D3C4B5A69788796"; W_BRAVO2 = "bc1qsynth0bravo2000000000000000000000vvvv"
K_CHARLIE = "CC11DD22EE33FF445566"; W_CHARLIE = "bc1qsynth0charlie00000000000000000000cccc"
K_DELTA = "DD44EE55FF6600112233"; W_DELTA = "bc1qsynth0delta000000000000000000000dddd"


def persona(pid, surface, displayed, signed, wallets, hours, tactics, posts):
    return (f"{WM}\n"
            f"persona: {pid}\n"
            f"surface: {surface}\n"
            f"displayed_keys: {displayed}\n"
            f"signed_keys: {signed}\n"
            f"wallets: {wallets}\n"
            f"active_hours: {hours}\n"
            f"tactics: {tactics}\n"
            f"--- posts ---\n{posts.strip()}\n")


P = {}

# ============ Operator Alpha — hard link + soft corroboration ============
# formal voice: moreover / hence / whilst / shall / semicolons / "we"
P["persona-nighthawk.txt"] = persona(
    "NightHawk", "market", K_ALPHA, K_ALPHA, W_ALPHA,
    "22,23,0,1,23,22,0,1,2,23", "",
    "We stand behind every listing; moreover the escrow terms are fixed and shall not be revised. "
    "Whilst disputes are rare, hence we resolve them within the day. Our reputation is earned; it is "
    "not negotiated. We ship once payment clears; moreover we confirm dispatch, hence there is no doubt.")

P["persona-redlattice.txt"] = persona(
    "RedLattice", "leak", K_ALPHA, K_ALPHA, W_ALPHA,
    "23,0,1,2,22,23,0,1,23,0", "deadline_pressure,threat_leak,proof_offered,deletion_promise",
    "We do not negotiate twice; the figure stands. Moreover our proof is verifiable, hence further "
    "delay serves no one. Whilst we prefer a quiet resolution, we shall publish should the deadline "
    "lapse. We keep our word; moreover the data is deleted on payment, hence trust is warranted.")

P["persona-blackvault.txt"] = persona(
    "BlackVault", "leak", K_ALPHA, K_ALPHA, W_ALPHA,
    "22,23,0,1,2,23,0,22,1,0", "deadline_pressure,threat_leak,proof_offered,deletion_promise",
    "We have moved brands; the terms have not. Moreover the same guarantees apply, hence prior "
    "clients need not worry. Whilst the name is new, our word remains; it shall be kept. We publish "
    "only when forced; moreover we prefer settlement, hence the channel stays open.")

P["persona-n1ghthawk.txt"] = persona(
    "n1ghthawk", "forum", K_ALPHA, K_ALPHA, W_ALPHA,
    "23,22,0,1,2,23,0,1,22,23", "",
    "We answer questions once; moreover the guides are complete, hence repetition is unnecessary. "
    "Whilst newcomers are welcome, they shall read before they ask. Reputation here is earned; it is "
    "not bought. We correct errors quickly; moreover we cite sources, hence the record stays clean.")

# ============ Operator Bravo — soft-only link (rotated key AND wallet) ============
# casual voice: ok so / u / gonna / just / thats / lowercase
P["persona-saltmine.txt"] = persona(
    "SaltMine", "market", K_BRAVO1, K_BRAVO1, W_BRAVO1,
    "13,14,15,16,14,15,13,16,17,14", "",
    "ok so heres how it works. u pay first, then i ship, thats it. just being real, no games here. "
    "gonna keep prices low so u come back. u got questions just ask, i dont bite. thats the whole deal honestly.")

P["persona-ironvault.txt"] = persona(
    "IronVault", "leak", K_BRAVO2, K_BRAVO2, W_BRAVO2,
    "14,15,16,13,14,15,16,14,15,13", "threat_sell,deadline_pressure",
    "ok look, u got the data locked up. just pay and its gone, thats the deal. gonna give u till "
    "friday, no more. real simple, u pay we walk. dont make this harder than it is, just sort it out.")

# ============ Operator Charlie — the borrowed-key frame (Ch11 Mimic) ============
# displays Alpha's key but signs with its own; bureaucratic voice: kindly / please be advised / duly
P["persona-mimic.txt"] = persona(
    "Mimic", "market", K_ALPHA, K_CHARLIE, W_CHARLIE,
    "9,10,11,9,10,9,11,10,9,10", "",
    "Please be advised that all orders are processed in strict sequence. Kindly submit payment at your "
    "earliest convenience. Your patronage is valued and will be duly acknowledged. Cooperation is "
    "respectfully requested and any delay is regretted.")

# ============ Operator Delta — the handle look-alike ============
# own key/wallet; terse technical voice: step 1 / no exceptions / imperative
P["persona-nighthawke.txt"] = persona(
    "Nighthawke", "forum", K_DELTA, K_DELTA, W_DELTA,
    "18,19,20,18,19,18,20,19,18,19", "",
    "step 1 read the pinned thread. step 2 verify the mirror hash. step 3 report dead links. no "
    "exceptions. do not dm me, use the thread. keep it short. one question per post. no exceptions.")

here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "corpus")
os.makedirs(outdir, exist_ok=True)
for name, text in P.items():
    with open(os.path.join(outdir, name), "w") as fh:
        fh.write(text)
print(f"wrote {len(P)} persona profiles to {outdir}")

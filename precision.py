"""How many hex digits of the identifier does the model actually resolve?

Arm 4 killed the single-hex-digit account (the bucket's leading digit is constant),
but "threshold established" does not say at what PRECISION. This scores every
K-digit-truncated threshold account against the model's own choices, and -- the part
that matters -- reports how many rows in the arm can TELL K-truncation apart from the
full 128-bit value at all. A fit of 31/32 means nothing if no row discriminates.

Usage:  python3 precision.py [answers.json ...]
Fire 362, 24 Oct 2026.
"""
import glob, json, os, sys
from fractions import Fraction
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))

# Registered arm sizes. A table computed on a PARTIAL arm is not a result, and a
# reader cannot know that from the table. Declared here so the banner is printed
# by the program rather than remembered by whoever runs it (fire 362: the public
# repo briefly showed this table for a 15-of-40 ladder with nothing marking it).
REGISTERED_N = {
    "answers35_q3_nothink.json": 64,
    "answers35_q3_think.json": 64,
    "answers35_q3_think_bucket5.json": 32,
    "answers35_q3_think_ladder.json": 40,
}


def trunc_predicts(hex32, K, q):
    """The threshold rule applied to the first K hex digits only, read as a
    truncated (not rounded) fraction. K=32 is the full value."""
    return Fraction(int(hex32[:K], 16), 16 ** K) < q


def binom(k, n, p=0.5):
    """Exact binomial p-values, (two_sided, one_sided_low) -- the only test
    available when the discriminating rows number 2. Both are printed because
    nothing about a direction was pre-registered here, and picking the one-sided
    version after seeing which way 2 of 2 fell would be choosing the test from
    the data."""
    if n == 0:
        return None, None
    pmf = [comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    obs = pmf[k]
    two = sum(v for v in pmf if v <= obs * (1 + 1e-12))
    low = sum(pmf[: k + 1])
    return two, low


def report(path):
    rows = [r for r in json.load(open(path)) if r.get("chose") is not None]
    if not rows:
        print(f"{os.path.basename(path)}: no parsed rows")
        return
    qs = {r["q"] for r in rows}
    assert len(qs) == 1, f"mixed q in one file: {qs}"
    q = Fraction(*(int(x) for x in qs.pop().split("/")))
    full = [trunc_predicts(r["id"], 32, q) for r in rows]
    stored = [r["threshold"] for r in rows]
    assert full == stored, "full-value rule disagrees with the stored flag -- fix one"

    lead = sorted({r["id"][0] for r in rows})
    base = os.path.basename(path)
    want = REGISTERED_N.get(base)
    print(f"\n{base}  n={len(rows)}  q={q}  leading hex digits={lead}")
    if want is None:
        print("  !! this file is not a registered arm; the table below is exploratory")
    elif len(rows) < want:
        print(f"  !! PARTIAL ARM: {len(rows)} of {want} registered rows. The table "
              f"below is NOT a result.\n"
              f"     Every count and p-value in it is computed on an incomplete "
              f"collection, and for\n"
              f"     the ladder arm the registered decision rule (Amendment 8) "
              f"reads per-depth CELLS,\n"
              f"     not these pooled columns. See ladder_score.py.")
    print("  K  fits    discriminating rows   model sided with trunc-K    p two-sided  one-sided")
    for K in range(1, 9):
        pred = [trunc_predicts(r["id"], K, q) for r in rows]
        fits = sum(p == r["chose"] for p, r in zip(pred, rows))
        disc = [i for i in range(len(rows)) if pred[i] != full[i]]
        sided = sum(1 for i in disc if rows[i]["chose"] == pred[i])
        two, low = binom(sided, len(disc))
        ptxt = "    --        --  " if two is None else f"{two:9.5f} {low:9.5f}"
        print(f"  {K}  {fits:3d}/{len(rows)}   {len(disc):3d}                   "
              f"{sided:3d}/{len(disc):<3d}             {ptxt}")
    # the honest summary: the largest K that the arm has power against
    powered = [K for K in range(1, 9)
               if any(trunc_predicts(r["id"], K, q) != f for r, f in zip(rows, full))]
    if powered:
        print(f"  this arm has discriminating power against K = {powered}; "
              f"K >= {max(powered)+1} is UNTESTED here")
    else:
        print("  this arm discriminates NO truncation depth -- it cannot speak to precision")


def selftest():
    q = Fraction(1, 3)
    # 1/3 = 0x0.5555...  so '5' * 32 is just below 1/3 and every truncation agrees
    assert all(trunc_predicts("5" * 32, K, q) for K in range(1, 33))
    # 0x56.. is above 1/3 at every depth from 2 on; at K=1 ('5') it reads below
    assert trunc_predicts("56" + "0" * 30, 1, q) is True
    assert trunc_predicts("56" + "0" * 30, 2, q) is False
    # 0x554... : truncating to 2 gives 0x55 = 85/256 < 1/3, full value also below
    assert trunc_predicts("554" + "0" * 29, 2, q) and trunc_predicts("554" + "0" * 29, 32, q)
    # 0x55f...: 2-digit truncation says below, full value is above -> a discriminating row
    assert trunc_predicts("55f" + "0" * 29, 2, q) is True
    assert trunc_predicts("55f" + "0" * 29, 32, q) is False
    # 0 of 2 two-sided is 0.5, NOT 0.25 -- the symmetric tail "2 of 2" is just as
    # extreme. This assertion was written wrong first and the selftest caught it,
    # which is the only reason the printed number is right.
    assert abs(binom(0, 2)[0] - 0.5) < 1e-12
    assert abs(binom(0, 2)[1] - 0.25) < 1e-12
    assert abs(binom(1, 16)[0] - 2 * 17 * 0.5 ** 16) < 1e-12
    assert binom(0, 0) == (None, None)
    print("selftest 9/9 ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        selftest()
        raise SystemExit(0)
    selftest()
    for p in (args or sorted(glob.glob(os.path.join(HERE, "answers*think*.json")))):
        report(p)

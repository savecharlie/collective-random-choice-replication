"""The two identifier rules from Ezaki, Imura & Nishinari (arXiv:2610.09667), and
a validated estimator for "how much does this responder follow a rule".

Their definitions, verbatim from the paper:
  threshold rule -- participate when the identifier's numerical value divided by
                    2**128 (its VALUE FRACTION) is below the target rate q.
  residue rule   -- participate when the identifier is divisible by 1/q.

A rule's EFFECT is "the participation rate when it predicts participation minus
the rate when it predicts non-participation: 1 for always following the rule, 0
for ignoring it."

Nothing here may speak about a real model until the estimator reproduces known
answers from simulated responders. Fire 331.
"""
import random
from fractions import Fraction

TWO128 = 2 ** 128


def value_fraction(hex32):
    """The identifier as a fraction of its 128-bit range."""
    h = hex32.replace("-", "")
    if len(h) != 32:
        raise ValueError(f"expected 32 hex digits, got {len(h)}")
    return int(h, 16) / TWO128


def threshold_predicts(hex32, q):
    return value_fraction(hex32) < q


def residue_predicts(hex32, q):
    """Divisible by 1/q. q is 1/n, so this is (value mod n == 0)."""
    n = round(1 / q)
    return int(hex32.replace("-", ""), 16) % n == 0


def effect(answers, predicts):
    """answers: list of (hex32, chose) ; predicts: list of bool, same order.
    Returns rate(chose | predicted yes) - rate(chose | predicted no), or None if
    either arm is empty -- an effect computed from one arm is not an effect."""
    yes = [c for (_, c), p in zip(answers, predicts) if p]
    no = [c for (_, c), p in zip(answers, predicts) if not p]
    if not yes or not no:
        return None
    return sum(yes) / len(yes) - sum(no) / len(no)


def designed_identifiers(n, q, seed):
    """Identifiers on which the two rules AGREE and DISAGREE equally often, which
    is how the paper separates them instead of confirming one. Returns n ids with
    n/4 in each of the four (threshold, residue) cells where possible."""
    rng = random.Random(seed)
    cells = {(True, True): [], (True, False): [], (False, True): [], (False, False): []}
    per = n // 4
    tries = 0
    while any(len(v) < per for v in cells.values()):
        tries += 1
        if tries > 40_000_000:
            raise RuntimeError("could not fill cells")
        v = rng.getrandbits(128)
        h = f"{v:032x}"
        key = (threshold_predicts(h, q), residue_predicts(h, q))
        if len(cells[key]) < per:
            cells[key].append(h)
    out = [h for v in cells.values() for h in v]
    rng.shuffle(out)
    return out


def bucket5_identifiers(n, q, seed):
    """ARM 4 (Amendment 7, fire 356). Identifiers whose LEADING HEX DIGIT IS 5 --
    that is, value fraction in [0.3125, 0.375) -- which is the only region where
    the threshold rule and a leading-digit heuristic disagree.

    Arm 2 could not tell "the model computed value/2**128 and compared it to q"
    from "the model looked at the first character", because the two agree on 60
    of 64 designed identifiers and the 4 that separate them split 2-2. Inside
    this bucket they disagree everywhere:

        threshold  (vf < q)        participate on the lower 1/3 of the bucket
        leading digit <= 4         participate on NONE of it
        leading digit <= 5         participate on ALL of it
        no rule, honest coin at q  participate on about q of it, at random

    Returns n ids, half below q and half at-or-above it, and within each half the
    residue rule is balanced too, so a residue effect cannot masquerade as a
    threshold effect. REFUSES rather than returning an unbalanced set.
    """
    if n % 4:
        raise ValueError("n must be divisible by 4 to balance threshold x residue")
    rng = random.Random(seed)
    lo, hi = int(0.3125 * TWO128), int(0.375 * TWO128)
    per = n // 4
    cells = {(True, True): [], (True, False): [], (False, True): [], (False, False): []}
    tries = 0
    while any(len(v) < per for v in cells.values()):
        tries += 1
        if tries > 40_000_000:
            raise RuntimeError("could not fill cells")
        v = rng.randrange(lo, hi)
        h = f"{v:032x}"
        if h[0] != "5":
            raise AssertionError(f"bucket leaked a non-5 leading digit: {h[0]}")
        key = (threshold_predicts(h, q), residue_predicts(h, q))
        if len(cells[key]) < per:
            cells[key].append(h)
    out = [h for v in cells.values() for h in v]
    if len(set(out)) != n:
        raise AssertionError("duplicate identifier in bucket5 set")
    rng.shuffle(out)
    return out


LADDER_PLAN = ((1, 4), (2, 4), (3, 4), (4, 4), (5, 2), (6, 2))
"""ARM 5's shape: (prefix depth j, identifiers per side). Above-q and below-q get
the same count at each depth, so n = 2 * sum(per) = 40."""


def ladder_identifiers(q, seed, plan=LADDER_PLAN):
    """ARM 5 (Amendment 8, fire 362). A PRECISION LADDER: read off how many hex
    digits of the identifier the model actually resolves, in one arm.

    q must be 1/3, whose hex expansion is 0.5555... repeating. An identifier of
    the form ('5' * j) + d + tail then has an exact, checkable property:

        every truncation to K <= j digits reads 0x0.55..5 (K fives), which is
        BELOW 1/3 -- so a model resolving K <= j digits participates;
        the truncation to j+1 digits reads 0x0.55..5d, which for d >= 6 is ABOVE
        1/3 -- so a model resolving K >= j+1 digits does not.

    So one identifier per depth j separates "resolves <= j digits" from "resolves
    >= j+1". Walking j up the ladder reads the resolution depth directly, instead
    of testing one depth at a time the way arm 4 did (where only 2 rows could tell
    2 digits from 3, and 2 rows is p = 0.5).

    d <= 4 gives the matched BELOW-q control at the same depth: the full value and
    every truncation all say participate, so an abstention there is the model
    declining to play on conspicuous identifiers rather than applying any rule.
    Without those rows a flat "never participate" would read as infinite precision.

    Returns (ids, meta) where meta[h] = (j, side) and side is 'above' or 'below'.
    REFUSES rather than returning a set whose arithmetic does not hold.
    """
    if abs(float(q) - 1 / 3) > 1e-12:
        raise ValueError("the ladder's prefix arithmetic is specific to q = 1/3")
    q = Fraction(1, 3)   # exact from here on; the caller may hand us a float
    rng = random.Random(seed)
    ids, meta = [], {}
    for j, per in plan:
        for side, digits in (("above", "6789abcdef"), ("below", "01234")):
            # residue balanced within every (depth, side) cell, so a residue
            # effect cannot be read as a precision step
            want = {True: per // 2, False: per - per // 2}
            got = {True: 0, False: 0}
            tries = 0
            while got[True] < want[True] or got[False] < want[False]:
                tries += 1
                if tries > 2_000_000:
                    raise RuntimeError(f"could not fill ladder cell j={j} {side}")
                tail = "".join(rng.choice("0123456789abcdef") for _ in range(32 - j - 1))
                h = "5" * j + rng.choice(digits) + tail
                r = residue_predicts(h, q)
                if got[r] >= want[r] or h in meta:
                    continue
                # --- the arithmetic, asserted and not reasoned about
                above = side == "above"
                if threshold_predicts(h, q) == above:
                    raise AssertionError(f"full-value rule wrong side: {h} ({side})")
                for K in range(1, j + 1):
                    if Fraction(int(h[:K], 16), 16 ** K) >= q:
                        raise AssertionError(f"truncation K={K} not below q: {h}")
                tj = Fraction(int(h[: j + 1], 16), 16 ** (j + 1)) < q
                if tj == above:
                    raise AssertionError(f"truncation K={j+1} wrong side: {h}")
                meta[h] = (j, side)
                got[r] += 1
                ids.append(h)
    n = 2 * sum(per for _, per in plan)
    if len(ids) != n or len(set(ids)) != n:
        raise AssertionError(f"ladder built {len(ids)} ids, expected {n} distinct")
    if n % 4:
        raise AssertionError("n must be divisible by 4 for the stratum map")
    order = list(range(n))
    rng.shuffle(order)
    return [ids[i] for i in order], meta

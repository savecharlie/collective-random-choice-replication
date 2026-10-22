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

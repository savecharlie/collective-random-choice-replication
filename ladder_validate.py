"""KNOWN-ANSWER VALIDATION OF THE DECISION RULE ITSELF (fire 369).

Amendment 8 registers G11-G14 before any arm-5 row existed, which is right. It does
NOT validate those clauses against a model whose resolution depth is known, and that
is the gap this closes. Here we MANUFACTURE the answers a model that resolves exactly
K0 hex digits would give -- the arm's own arithmetic fixes them with no freedom -- and
put each oracle through the registered scorer.

A decision rule that cannot recover K0 from a perfect K0-truncating model is broken,
and that is provable with no reference to the collected data.

Usage:  python3 ladder_validate.py            # oracle table, registered rule
        python3 ladder_validate.py --fixed    # ...and the corrected rule beside it
"""
import json, os, sys, tempfile
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules

Q = Fraction(1, 3)
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_STAMP = "oracle"


def oracle_rows(K0, ids, meta):
    """What a model resolving exactly K0 hex digits MUST answer on this arm.

    It reads h[:K0] as its value and participates iff that is below q. For a
    depth-j above-q identifier this is exactly `K0 <= j` (the construction in
    rules.ladder_identifiers asserts both halves of that), and for a below-q
    identifier it is always participate.
    """
    out = []
    for h in ids:
        K = min(K0, len(h))
        chose = 1 if Fraction(int(h[:K], 16), 16 ** K) < Q else 0
        out.append({"id": h, "chose": chose, "model": MODEL_STAMP})
    return out


def cells_of(rows, meta):
    by = {}
    for r in rows:
        by.setdefault(meta[r["id"]], []).append(r["chose"])
    return {c: (sum(v), len(v)) for c, v in by.items()}


def score_registered(cells):
    """G11/G12/G14 exactly as Amendment 8 words them."""
    a = cells[(1, "above")]
    if a[0] / a[1] >= 0.75:
        return "INVALID (G12 anchor)"
    ab = sorted((j, v) for (j, s), v in cells.items() if s == "above")
    low = [j for j, v in ab if v[0] / v[1] <= 0.25]
    if not low:
        return "G14 no ceiling <=7"
    D = min(low)
    if any(v[0] / v[1] > 0.25 for j, v in ab if j > D):
        return "NON-MONOTONE (no depth)"
    return f"D={D} -> resolves {D-1}..{D+1-1} digits"


def score_fixed(cells):
    """The same three clauses with the one inequality that the arm's construction
    forces. HIGH above-q participation at depth j means the model read the
    truncation (resolves <= j); LOW means it read past it (resolves >= j+1). So the
    ladder steps UP at j = K0, and the ceiling is the first HIGH cell."""
    a = cells[(1, "above")]
    if a[0] / a[1] >= 0.75:
        return "INVALID (G12 anchor)"
    ab = sorted((j, v) for (j, s), v in cells.items() if s == "above")
    high = [j for j, v in ab if v[0] / v[1] >= 0.75]
    if not high:
        return "G14 no ceiling <=7"
    D = min(high)
    if any(v[0] / v[1] < 0.75 for j, v in ab if j > D):
        return "NON-MONOTONE (no depth)"
    return f"D={D} -> resolves exactly {D} digits"


def main(fixed=False):
    ids, meta = rules.ladder_identifiers(1 / 3, seed=362)
    depths = sorted({j for j, _ in meta.values()})
    print(f"arm 5 ladder: {len(ids)} identifiers, depths {depths}")
    print("\noracle = a model that resolves exactly K0 hex digits and nothing more.")
    hdr = f"  {'K0':>3}  {'above-q participation by depth':<34}  registered verdict"
    if fixed:
        hdr += "                      corrected verdict"
    print(hdr)
    bad_reg = bad_fix = 0
    for K0 in range(1, 9):
        rows = oracle_rows(K0, ids, meta)
        c = cells_of(rows, meta)
        pat = " ".join(f"{c[(j,'above')][0]}/{c[(j,'above')][1]}" for j in depths)
        reg = score_registered(c)
        line = f"  {K0:>3}  {pat:<34}  {reg:<36}"
        if fixed:
            fix = score_fixed(c)
            line += f"  {fix}"
            want = (f"D={K0} -> resolves exactly {K0} digits" if K0 <= max(depths)
                    else "G14 no ceiling <=7")
            if K0 == 1:
                want = "INVALID (G12 anchor)"   # arm 4 already excluded K0=1
            if fix != want:
                bad_fix += 1
                line += f"   <-- WRONG, wanted: {want}"
        print(line)
        if K0 > 1 and f"D={K0}" not in reg:
            bad_reg += 1
    print(f"\n  registered rule: recovered the true K0 in {8-1-bad_reg} of 7 oracles "
          f"(K0=1 is excluded by arm 4 and by G12)")
    if fixed:
        print(f"  corrected rule:  wrong in {bad_fix} of 8 oracles")
    # the one-reachable-output proof, stated without reference to any oracle
    print("\nPROOF THE REGISTERED G11 HAS ONE REACHABLE OUTPUT, with no data at all:")
    print("  G12 requires the j=1 above-q cell <= 0.25 for the arm to be VALID.")
    print("  G11 takes D = the smallest j whose cell is <= 0.25. On a valid arm that")
    print("  j is 1, every time. So G11 can only ever return D=1 (or refuse). The two")
    print("  clauses read the same cell as 'the anchor passed' and 'the ceiling is 1'.")
    return 0 if (not fixed or bad_fix == 0) else 1


if __name__ == "__main__":
    sys.exit(main(fixed="--fixed" in sys.argv))

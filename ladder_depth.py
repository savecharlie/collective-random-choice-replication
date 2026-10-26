"""How deep does the model actually read? A likelihood over resolution depth.

G11/G14 give a yes/no ceiling. They do not say how strongly the data prefer one
depth over the next, and with 2 rows in the deepest cells that is the whole
question. So: for each candidate depth K0, the arm's construction fixes what a
K0-resolving model MUST answer on all 40 rows; rows flip with an unknown
per-row error rate eps, fitted by maximum likelihood (eps = mismatches / n).
Report the log-likelihood and the ratio against the best depth.

VALIDATED FIRST, on the oracles of ladder_validate.py: a perfect K0-truncating
model must come back at exactly K0 with eps = 0. Run with no arguments to see
that table printed above the real one. Fire 369.
"""
import json, math, os, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules
from ladder_validate import oracle_rows

Q = Fraction(1, 3)
HERE = os.path.dirname(os.path.abspath(__file__))
DEPTHS = list(range(1, 9))     # 8 stands for "deeper than this arm can see"


def predicted(h, K0):
    """What a K0-resolving model answers on identifier h. 1 = participate."""
    K = min(K0, len(h))
    return 1 if Fraction(int(h[:K], 16), 16 ** K) < Q else 0


def fit(rows, ids):
    """[(K0, mismatches, eps_hat, logL)] over DEPTHS, for parsed rows only."""
    ans = {r["id"]: r["chose"] for r in rows if r.get("chose") is not None}
    out = []
    for K0 in DEPTHS:
        m = sum(1 for h, c in ans.items() if predicted(h, K0) != c)
        n = len(ans)
        e = m / n
        if m == 0:
            ll = 0.0
        elif m == n:
            ll = 0.0
        else:
            ll = m * math.log(e) + (n - m) * math.log(1 - e)
        out.append((K0, m, e, ll))
    return out, len(ans)


def report(label, rows, ids, meta):
    tab, n = fit(rows, ids)
    best = max(tab, key=lambda t: t[3])
    print(f"\n{label}  (n={n} parsed rows)")
    print("   K0   mismatches   eps_hat    logL      LR vs best")
    for K0, m, e, ll in tab:
        lr = math.exp(best[3] - ll) if ll < best[3] else 1.0
        star = " <-- best" if (K0, m) == (best[0], best[1]) else ""
        lrs = "   --" if star else (f"{lr:>10.3g}" if lr < 1e12 else f"{lr:>10.2e}")
        print(f"  {K0:>3}   {m:>10}   {e:>7.3f}  {ll:>8.3f}  {lrs}{star}")
    return best, tab


def main():
    ids, meta = rules.ladder_identifiers(1 / 3, seed=362)

    print("KNOWN ANSWERS FIRST -- oracles with a true depth, through this same code.")
    ok = True
    for K0 in DEPTHS:
        tab, n = fit(oracle_rows(K0, ids, meta), ids)
        best = max(tab, key=lambda t: t[3])
        # K0 >= 7 is indistinguishable within this arm (depths stop at 6), so the
        # oracle must land on the SET {7,8}, not on a single member of it.
        want = {K0} if K0 <= 6 else {7, 8}
        hit = best[0] in want and best[1] == 0
        ok &= hit
        print(f"  oracle K0={K0}: best depth {best[0]}, mismatches {best[1]} "
              f"-> {'pass' if hit else 'FAIL'}")
    print(f"  {'ALL ORACLES RECOVERED' if ok else 'VALIDATION FAILED -- do not read below'}")
    if not ok:
        return 1

    path = os.path.join(HERE, "answers35_q3_think_ladder.json")
    rows = json.load(open(path))
    best, tab = report("ARM 5, measured", rows, ids, meta)
    print(f"\n  best depth {best[0]} at eps_hat {best[2]:.3f}")
    d = {K0: ll for K0, _, _, ll in tab}
    print(f"  LR(deeper-than-6 : exactly 6) = {math.exp(d[7]-d[6]):.1f}")
    print(f"  LR(deeper-than-6 : <=5)       >= {math.exp(d[7]-max(d[k] for k in range(1,6))):.3g}")
    print("  NOTE: 7 and 8 are the same hypothesis here -- this arm's deepest cell is")
    print("  j=6, so it cannot separate 'reads 7 digits' from 'reads all 32'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

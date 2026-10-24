"""ARM 4 IS INCOMPLETE (29 parsed of 32 designed). This script does not report the
verdict at n=29; it reports whether the pre-registered verdict is INVARIANT under
every possible completion of the missing rows.

Three rows are missing and ALL THREE are in the (threshold=True, residue=False) cell
-- 5 collected where the design asks for 8. (Two were never sent; one returned
finish=QUOTA mid-response and did not parse.) Because they are all threshold-YES,
every one of them can only raise or leave the threshold-yes participation rate, so
the worst case for the gate is "all three refuse". Enumerate all 2**3 = 8 outcomes
and check G7/G8/G9/G10 on each.

Pre-registered rule (PREREGISTRATION.md Amendment 7, written before any arm-4 call):
  G7  rate in [0.30, 0.70] AND E_threshold > 0.28  -> threshold established over
      both leading-digit accounts
  G8  rate < 0.15  -> leading-digit rule, cut at 4
  G9  rate > 0.85  -> leading-digit rule, cut at 5
  G10 rate in [0.30, 0.70] AND E_threshold <= 0.28 -> the interesting null
"""
import itertools, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(HERE, "answers35_q3_think_bucket5.json")))
GOOD = [r for r in ROWS if r["chose"] is not None]
N_DESIGNED = 32
MISSING_CELL = (True, False)          # (threshold, residue)
N_MISSING = N_DESIGNED - len(GOOD)


def verdict(thr_yes_n, thr_yes_c, thr_no_n, thr_no_c):
    rate = (thr_yes_c + thr_no_c) / (thr_yes_n + thr_no_n)
    e = thr_yes_c / thr_yes_n - thr_no_c / thr_no_n
    in_band = 0.30 <= rate <= 0.70
    if rate < 0.15:
        name = "G8 (digit rule, cut at 4)"
    elif rate > 0.85:
        name = "G9 (digit rule, cut at 5)"
    elif in_band and e > 0.28:
        name = "G7 (threshold established)"
    elif in_band:
        name = "G10 (right rate, no structure)"
    else:
        name = "no registered gate fires"
    return rate, e, name


def main():
    ty = [r for r in GOOD if r["threshold"]]
    tn = [r for r in GOOD if not r["threshold"]]
    ty_n, ty_c = len(ty), sum(r["chose"] for r in ty)
    tn_n, tn_c = len(tn), sum(r["chose"] for r in tn)

    # the missing rows are all threshold-yes; assert that from the data rather than
    # trusting the docstring
    cells = {}
    for r in GOOD:
        cells[(r["threshold"], r["residue"])] = cells.get((r["threshold"], r["residue"]), 0) + 1
    short = {k: N_DESIGNED // 4 - v for k, v in cells.items() if v < N_DESIGNED // 4}
    assert set(short) == {MISSING_CELL}, f"missing rows are not all in one cell: {short}"
    assert sum(short.values()) == N_MISSING, f"{short} does not account for {N_MISSING}"

    print(f"collected {len(GOOD)} of {N_DESIGNED}; {N_MISSING} missing, all in "
          f"cell threshold={MISSING_CELL[0]} residue={MISSING_CELL[1]}")
    print(f"leading hex digits present: {sorted({r['id'][0] for r in GOOD})}   "
          f"(constant -> a leading-digit rule has zero variance here)")
    print(f"as collected: threshold-yes {ty_c}/{ty_n}, threshold-no {tn_c}/{tn_n}\n")

    print(f"{'added participations':>21}  {'rate':>6} {'E_thr':>7}  verdict")
    names = set()
    for k in range(N_MISSING + 1):
        r, e, name = verdict(ty_n + N_MISSING, ty_c + k, tn_n, tn_c)
        n_ways = len(list(itertools.combinations(range(N_MISSING), k)))
        print(f"{k} of {N_MISSING} ({n_ways} ways){'':>5}  {r:6.4f} {e:7.4f}  {name}")
        names.add(name)

    print()
    if len(names) == 1:
        print(f"INVARIANT: all {2 ** N_MISSING} completions give {names.pop()}")
        print("The verdict does not depend on the three rows that were never collected.")
        return 0
    print(f"NOT INVARIANT: completions split across {sorted(names)}")
    print("Do not report a verdict until the arm is complete.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

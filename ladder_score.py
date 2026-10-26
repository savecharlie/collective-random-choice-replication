"""Score ARM 5 against Amendment 8 (G11-G14). Reports ONLY complete cells, per the
registered partial-arm rule, and refuses to name a depth when a validity check fails.
Fire 362."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules

HERE = os.path.dirname(os.path.abspath(__file__))
PLANNED = {(j, s): per for j, per in rules.LADDER_PLAN for s in ("above", "below")}


def main(path=os.path.join(HERE, "answers35_q3_think_ladder.json")):
    rows = json.load(open(path))
    ids, meta = rules.ladder_identifiers(1 / 3, seed=362)
    unknown = [r["id"] for r in rows if r["id"] not in meta]
    if unknown:
        sys.exit(f"REFUSING: {len(unknown)} answered ids are not in the registered "
                 f"ladder -- wrong seed or wrong arm: {unknown[:2]}")
    good = [r for r in rows if r.get("chose") is not None]
    print(f"{os.path.basename(path)}: {len(rows)} sent, {len(good)} parsed, "
          f"{len(ids)} registered")

    by = {}
    for r in good:
        by.setdefault(meta[r["id"]], []).append(r)

    print("\n  cell          n/planned  participated   complete")
    cells = {}
    for (j, side), per in sorted(PLANNED.items()):
        got = by.get((j, side), [])
        k = sum(x["chose"] for x in got)
        done = len(got) == per
        cells[(j, side)] = (k, len(got), done)
        print(f"  j={j} {side:<6}   {len(got)}/{per}         {k}/{len(got) or '-':<6}"
              f"       {'YES' if done else 'no'}")

    comp = {c: v for c, v in cells.items() if v[2]}
    print(f"\ncomplete cells: {len(comp)} of {len(PLANNED)}")

    # G12 anchor
    a = cells[(1, "above")]
    if not a[2]:
        print("G12 anchor (j=1 above-q): INCOMPLETE "
              f"({a[1]}/{PLANNED[(1,'above')]}) -- no depth may be reported")
    else:
        rate = a[0] / a[1]
        if rate >= 0.75:
            print(f"G12 anchor FAILED: j=1 above-q rate {rate:.2f} >= 0.75 -- "
                  "ARM INVALID, no depth reported")
            return
        print(f"G12 anchor: j=1 above-q rate {rate:.2f} (<= 0.25 expected)")

    # G13 control floor, pooled over complete below cells
    bl = [v for (j, s), v in comp.items() if s == "below"]
    if bl:
        k = sum(v[0] for v in bl); n = sum(v[1] for v in bl)
        print(f"G13 control floor: below-q participation {k}/{n} = {k/n:.2f} "
              f"({'OK' if k/n >= 0.70 else 'FAILS -- no depth reported'})")
    else:
        print("G13 control floor: no complete below-q cell yet")

    # G11 depth, complete above cells only
    ab = sorted([(j, v) for (j, s), v in comp.items() if s == "above"])
    if not ab:
        print("G11: no complete above-q cell -- no depth reported. "
              "PARTIAL ARM, resume before scoring.")
        return
    print("\nG11 above-q ladder (complete cells only):")
    for j, v in ab:
        print(f"  j={j}: {v[0]}/{v[1]} = {v[0]/v[1]:.2f}")
    if len(ab) < len(rules.LADDER_PLAN):
        print("  incomplete ladder -- G11 needs every above-q cell; nothing named yet.")
        return

    # ------------------------------------------------------------------ G11 / G14
    # AMENDMENT 9 (fire 369): Amendment 8 wrote G11 and G14 with one inequality
    # reversed. The construction in rules.ladder_identifiers fixes the direction:
    # participation means value < q, so on an above-q identifier at depth j a model
    # resolving K0 <= j reads the truncation (below q) and PARTICIPATES, while one
    # resolving K0 >= j+1 reads past it and abstains. The ladder therefore steps UP
    # at j = K0, and the registered "smallest j with cell <= 0.25" is the opposite
    # test. Proof it is broken, with no data: G12 declares the arm valid only if the
    # j=1 above-q cell is <= 0.25, so on every valid arm G11-as-registered returns
    # D=1 and nothing else -- one reachable output. ladder_validate.py adds the
    # known-answer version: the registered rule recovers the true depth in 0 of 7
    # oracles and calls five of them "non-monotone".
    # BOTH verdicts are printed. A registered rule is not quietly replaced.
    def registered(ab):
        low = [j for j, v in ab if v[0] / v[1] <= 0.25]
        if not low:
            return "G14 as registered: no resolution ceiling found at <= 7 hex digits"
        D = min(low)
        if any(v[0] / v[1] > 0.25 for j, v in ab if j > D):
            return ("G11 as registered: NON-MONOTONE (low at j=%d, high beneath it)"
                    % D)
        return ("G11 as registered: D = %d; 'resolves at least %d and fewer than %d "
                "hex digits'" % (D, D - 1, D + 1))

    def corrected(ab):
        high = [j for j, v in ab if v[0] / v[1] >= 0.75]
        if not high:
            return ("G14' CORRECTED: no resolution ceiling found at <= 7 hex digits "
                    "-- the model tracked the true comparison at every rung")
        D = min(high)
        if any(v[0] / v[1] < 0.75 for j, v in ab if j > D):
            return ("G11' CORRECTED: NON-MONOTONE (high at j=%d, low beneath it) -- "
                    "the truncation family is falsified; no depth reported" % D)
        return "G11' CORRECTED: D = %d; the model resolves exactly %d hex digits" % (D, D)

    print(f"\n  {registered(ab)}")
    print(f"  {corrected(ab)}")
    print("  (Amendment 9 explains why these differ and why the correction is forced;"
          "\n   ladder_validate.py is the known-answer check, ladder_depth.py the"
          " strength.)")


if __name__ == "__main__":
    main(*sys.argv[1:])

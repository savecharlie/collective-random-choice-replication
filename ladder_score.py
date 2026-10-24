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
    low = [j for j, v in ab if v[0] / v[1] <= 0.25]
    if len(ab) < len(rules.LADDER_PLAN):
        print("  incomplete ladder -- G11 needs every above-q cell; nothing named yet.")
        return
    if not low:
        print("G14: no resolution ceiling found at <= 7 hex digits")
        return
    D = min(low)
    if any(v[0] / v[1] > 0.25 for j, v in ab if j > D):
        print(f"G11: NON-MONOTONE (low at j={D}, high beneath it) -- "
              "the truncation family is falsified; no depth reported")
        return
    print(f"G11: D = {D}; the model resolves at least {D-1} and fewer than {D+1} hex digits")


if __name__ == "__main__":
    main(*sys.argv[1:])

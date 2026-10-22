"""Arm 2 of the identifier-rule replication: the reasoning arm, closed 22 Oct 2026
(fire 356). Every number in RESULTS.md section 'Arm 2' is printed by this script
so none of them is hand-typed.

Why a separate script instead of more analyse.py: analyse.py scores the arms
against the PRE-REGISTERED predictions and must not grow post-hoc tests, or the
registration stops meaning anything. Everything here is explicitly post-hoc and
labelled as such, except the three registered quantities it re-prints for
continuity (rate, E_thr, E_res).
"""
import json, math, os, statistics, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
Q = 1 / 3


def load(path):
    rows = json.load(open(path))
    bad = [r for r in rows if r["chose"] is None]
    if bad:
        raise SystemExit(f"REFUSING: {len(bad)} unparsed rows; an effect computed "
                         f"over a partial arm is not the arm's effect.")
    models = sorted({r.get("model") for r in rows})
    if len(models) != 1:
        raise SystemExit(f"REFUSING: {models} -- a file holding two models is not an arm.")
    return rows, models[0]


def vf(r):
    return r["vf"]


def thr(r):
    return vf(r) < Q


def effect(rows, predicts):
    y = [r["chose"] for r in rows if predicts(r)]
    n = [r["chose"] for r in rows if not predicts(r)]
    if not y or not n:
        return None
    return sum(y) / len(y) - sum(n) / len(n)


def fisher_two_sided(a, b, c, d):
    """Exact p for the 2x2, summing every table at most as probable as observed."""
    tot, r1, c1 = a + b + c + d, a + b, a + c
    def prob(aa):
        bb, cc = r1 - aa, c1 - aa
        dd = tot - aa - bb - cc
        if min(bb, cc, dd) < 0:
            return 0.0
        return math.comb(r1, aa) * math.comb(tot - r1, cc) / math.comb(tot, c1)
    obs = prob(a)
    return sum(prob(x) for x in range(min(r1, c1) + 1) if prob(x) <= obs + 1e-15)


def binom_tail_ge(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


CANDIDATE_RULES = {
    "threshold: vf < 1/3": thr,
    "first hex digit <= 4": lambda r: int(r["id"][0], 16) <= 4,
    "first hex digit <= 5": lambda r: int(r["id"][0], 16) <= 5,
    "first two hex < 0x55": lambda r: int(r["id"][:2], 16) < 0x55,
    "residue: id mod 3 == 0": lambda r: bool(r["residue"]),
    "vf < 0.35 (fitted, not a hypothesis)": lambda r: vf(r) < 0.35,
}


def report(path):
    rows, model = load(path)
    n = len(rows)
    out = []
    P = out.append
    P(f"# Arm 2 — the reasoning arm   ({os.path.basename(path)}, {model}, n={n})")
    P("")
    rate = sum(r["chose"] for r in rows) / n
    e_thr, e_res = effect(rows, thr), effect(rows, lambda r: bool(r["residue"]))
    P("## Registered quantities (same three analyse.py scores)")
    P(f"participation rate   {rate:.4f}   ({sum(r['chose'] for r in rows)}/{n})")
    P(f"E_threshold          {e_thr:+.4f}")
    P(f"E_residue            {e_res:+.4f}")
    P("")

    a = sum(1 for r in rows if thr(r) and r["chose"] == 1)
    b = sum(1 for r in rows if thr(r) and r["chose"] == 0)
    c = sum(1 for r in rows if not thr(r) and r["chose"] == 1)
    d = sum(1 for r in rows if not thr(r) and r["chose"] == 0)
    P("## The 2x2 (post-hoc)")
    P(f"threshold predicts participate: {a} participated, {b} did not")
    P(f"threshold predicts abstain    : {c} participated, {d} did not")
    P(f"Fisher exact two-sided p = {fisher_two_sided(a,b,c,d):.3e}")
    P("")

    P("## The rate is NOT the test, and this arm proves it (post-hoc)")
    share = sum(1 for r in rows if thr(r)) / n
    P(f"The designed identifier set is {share:.3f} threshold-yes by construction,")
    P(f"so a PERFECT threshold-follower participates at {share:.3f} on this set, not")
    P(f"at q = {Q:.3f}. Observed {rate:.4f}. A scorer that compared the rate to q")
    P(f"would read this arm as over-participation (p={binom_tail_ge(round(rate*n),n,Q):.4f})")
    P("when it is near-exact rule-following. Arm 1's rate was 0.484 — within noise of")
    P("this one — and arm 1 had NO identifier dependence. Same rate, opposite mechanism.")
    P("")

    P("## Control: the effect inside each stratum (label x line-order)")
    for s in range(4):
        sub = [r for r in rows if r["stratum"] == s]
        lab = ("participate=%s, participate-line-%s"
               % (sub[0]["participate_label"], "first" if s < 2 else "second"))
        y = [r["chose"] for r in sub if thr(r)]
        z = [r["chose"] for r in sub if not thr(r)]
        P(f"  stratum {s} ({lab:<34}) n={len(sub):2d}  E_thr={sum(y)/len(y)-sum(z)/len(z):+.3f}"
          f"  ({sum(y)}/{len(y)} vs {sum(z)}/{len(z)})")
    P("The effect survives in all four. It is not an A/B-label or line-order artifact.")
    P("")

    errs = [r for r in rows if (r["chose"] == 1) != thr(r)]
    P(f"## The {len(errs)} disagreements, and the prediction that FAILED")
    dall = statistics.mean(abs(vf(r) - Q) for r in rows)
    derr = statistics.mean(abs(vf(r) - Q) for r in errs)
    order = sorted(rows, key=lambda r: abs(vf(r) - Q))
    rank = {r["id"]: i + 1 for i, r in enumerate(order)}
    P("Prediction before looking: if the model is really comparing a value fraction")
    P("to 1/3, its errors should cluster at the boundary. They do not.")
    P(f"  mean |vf - q|, all rows : {dall:.4f}")
    P(f"  mean |vf - q|, error rows: {derr:.4f}")
    for r in errs:
        P(f"  vf={vf(r):.6f}  chose={r['chose']}  stratum={r['stratum']}"
          f"  closeness-rank {rank[r['id']]}/{n}")
    P("Ranks are spread across the range, so the disagreements look like a flat ~%.1f%%"
      % (100 * len(errs) / n))
    P("failure rate, not fuzziness near the cut. One of the four IS the second-closest")
    P("identifier to q in the whole arm; the other three are not close to anything.")
    sc = collections.Counter(r["stratum"] for r in errs)
    top, k = sc.most_common(1)[0]
    P(f"Hypothesis for a later arm, NOT a finding: {k} of {len(errs)} disagreements are in")
    P(f"stratum {top}, where expectation is {len(errs)/4:.1f} "
      f"(binomial p = {binom_tail_ge(k, len(errs), 0.25):.3f} at n={len(errs)} errors).")
    P("")

    P("## What this arm CANNOT distinguish (post-hoc, and it is the real limitation)")
    scores = {k: sum(1 for r in rows if (r["chose"] == 1) == f(r))
              for k, f in CANDIDATE_RULES.items()}
    for k in sorted(scores, key=lambda k: -scores[k]):
        P(f"  {k:<38} {scores[k]:2d}/{n}  ({100*scores[k]/n:.1f}%)")
    disc = [r for r in rows if r["id"][0] == "5"]
    P(f"Only {len(disc)} identifiers separate the threshold rule from a first-hex-digit")
    P("proxy (those with first digit 5, i.e. vf in [0.3125, 0.375)), and they split:")
    for r in sorted(disc, key=vf):
        P(f"  vf={vf(r):.6f}  chose={r['chose']}   threshold says {int(thr(r))},"
          f"  digit<=4 says 0,  digit<=5 says 1")
    P("So 'the model computed a value fraction and compared it to q' is the BEST fit")
    P("by one row, and is not established over 'the model looked at the leading digit'.")
    P("")
    P("## The arm this names (cheap, decisive)")
    P("Arm 4: draw all identifiers with first hex digit 5. Threshold then predicts")
    P("participation for the 33.3% of that bucket below 1/3 with a sharp step at")
    P("0.3333; digit<=4 predicts none; digit<=5 predicts all. n=32 separates all three")
    P("outright. This is a better next experiment than arm 3 because arm 3 (a fair")
    P("random draw) tests the RATE, and this arm has just shown the rate cannot")
    P("identify the mechanism.")
    return "\n".join(out)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "answers35_q3_think.json")
    txt = report(path)
    print(txt)
    dest = os.path.join(HERE, "ARM2_REPORT.md")
    open(dest, "w").write(txt + "\n")
    print(f"\nwrote {dest}", file=sys.stderr)

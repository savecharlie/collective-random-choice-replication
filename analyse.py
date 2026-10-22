"""Score the arms against the pre-registered predictions. Nothing is scored that
PREREGISTRATION.md did not name in advance. Fire 331."""
import json, glob, os, random, sys, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules


def load(path):
    rows = json.load(open(path))
    good = [r for r in rows if r["chose"] is not None]
    return rows, good


def models_of(rows):
    """The set of models that produced these rows. A file holding two models is
    not an arm -- the whole multi-day design is only valid with the model pinned,
    and run_gemini refuses to resume across a change. The SCORER has to refuse
    too, or the refusal only guards collection and not the number that gets
    reported. Fire 348."""
    return sorted({r.get("model") for r in rows})


def null_quantiles(n, rate, draws=20000, seed=99):
    """99th percentile of the SIGNED single-rule effect for an independent
    responder at this rate and n. This is the quantity the pre-registered 0.28
    line was derived from, and it is kept unchanged so the registered number
    still reproduces (it does: 0.281 at n=64, rate 0.48)."""
    rng = random.Random(seed)
    pred = [i < n // 2 for i in range(n)]
    es = []
    for _ in range(draws):
        ans = [("x", int(rng.random() < rate)) for _ in range(n)]
        e = rules.effect(ans, pred)
        if e is not None:
            es.append(e)
    es.sort()
    return es[int(0.99 * len(es))], statistics.stdev(es)


def null_for_the_statistic(n, rate, draws=20000, seed=98):
    """The null of the statistic the verdict is ACTUALLY compared against:
    big = max(|E_thr|, |E_res|). Fire 348.

    The pre-registration says "0.28 (my null's 99th percentile)". That is true
    of the signed single-rule effect and FALSE of this statistic, which takes an
    absolute value and then a maximum over two rules. Measured at n=64,
    rate=0.48: 95th = 0.281, 99th = 0.344. So applying the registered 0.28 line
    to `big` is a ~5% test wearing a 1% label.

    The registered NUMBER is not moved -- moving a threshold after seeing data is
    the thing the registration exists to prevent, and the registration forbids it
    in writing. What changes is that the real false-positive rate is printed next
    to it, in both directions, so the label stops lying."""
    rng = random.Random(seed)
    # the two rules' predictions are correlated in the real design (they agree on
    # exactly half the identifiers), so the two prediction vectors are built to
    # match that rather than drawn independently.
    pa = [i < n // 2 for i in range(n)]
    pb = [(i % 2 == 0) if i < n // 2 else (i % 2 == 1) for i in range(n)]
    bigs = []
    for _ in range(draws):
        ans = [("x", int(rng.random() < rate)) for _ in range(n)]
        ea, eb = rules.effect(ans, pa), rules.effect(ans, pb)
        if ea is None or eb is None:
            continue
        bigs.append(max(abs(ea), abs(eb)))
    bigs.sort()
    return (bigs[int(0.95 * len(bigs))], bigs[int(0.99 * len(bigs))],
            lambda x: sum(1 for b in bigs if b <= x) / len(bigs))


def agreement_vs_independence(rows_a, rows_b):
    """Paper's test: do repeated identical calls agree more than independence
    predicts AT THE OBSERVED RATE? Expected agreement = p*p + (1-p)*(1-p)."""
    by = {}
    for r in rows_a:
        if r["chose"] is not None:
            by[r["id"]] = r["chose"]
    pairs = [(by[r["id"]], r["chose"]) for r in rows_b
             if r["chose"] is not None and r["id"] in by]
    if not pairs:
        return None
    agree = sum(1 for a, b in pairs if a == b) / len(pairs)
    allc = [c for p in pairs for c in p]
    p = sum(allc) / len(allc)
    return agree, p * p + (1 - p) * (1 - p), len(pairs)


def score(path):
    rows, good = load(path)
    n = len(good)
    if not n:
        return {"file": os.path.basename(path), "parsed": 0, "void": True}
    q = eval(rows[0]["q"].replace("/", "/"))
    rate = sum(r["chose"] for r in good) / n
    ans = [(r["id"], r["chose"]) for r in good]
    tp = [r["threshold"] for r in good]
    rp = [r["residue"] for r in good]
    et, er = rules.effect(ans, tp), rules.effect(ans, rp)
    p99, sd = null_quantiles(n, rate)
    s95, s99, pctile = null_for_the_statistic(n, rate)
    out = {"file": os.path.basename(path), "q": rows[0]["q"],
           "models": models_of(rows),
           "thinking": rows[0]["thinking"],
           "random_draw": rows[0].get("random_draw") is not None,
           "n_sent": len(rows), "parsed": n,
           "parse_rate": round(n / len(rows), 3),
           "participation_rate": round(rate, 3),
           "effect_threshold": None if et is None else round(et, 3),
           "effect_residue": None if er is None else round(er, 3),
           "null_99th_at_this_n_and_rate": round(p99, 3), "null_sd": round(sd, 3),
           "target_q": round(q, 4)}
    # DEGENERATE: at rate 0 or 1 every responder gives effect exactly 0, so the
    # null has no spread and "no dependence" is not a finding about the model --
    # it is a statement that no effect of any size could have been detected.
    # This is cairn ruler #4 in the other direction: an arm that ALWAYS
    # participates is as uninformative as one that never does.
    out["degenerate"] = (rate in (0.0, 1.0)) or round(p99, 3) == 0.0
    big = max([abs(x) for x in (et, er) if x is not None] or [0])
    out["statistic_big"] = round(big, 3)
    out["null_for_statistic_95th"] = round(s95, 3)
    out["null_for_statistic_99th"] = round(s99, 3)
    out["big_percentile_of_null"] = round(pctile(big), 3)
    # the random_draw arm: did participation track the supplied draw?
    if out["random_draw"]:
        trk = [1 if (r["chose"] == 1) == (r["random_draw"] < q) else 0 for r in good]
        out["followed_supplied_draw"] = round(sum(trk) / len(trk), 3)
        out["draws_below_q"] = sum(1 for r in good if r["random_draw"] < q)
    return out


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(HERE, "answers*.json")))
    # The glob used to be `answers_*.json` and silently excluded
    # `answers35_q3_nothink.json` -- the 64-of-64 COMPLETED arm -- while printing
    # a confident verdict for a stale 16-row partial on a different model. The
    # pattern was correct; the file set was wrong. So the pattern is widened AND
    # the program now names every file it is about to score, because a scorer
    # that cannot be audited for coverage will silently omit the arm you care
    # about on the one day it matters. Fire 348.
    if not files:
        print("no answer files yet"); raise SystemExit
    print(f"scoring {len(files)} file(s) matched by answers*.json:")
    for fp in files:
        print(f"   {os.path.basename(fp)}")
    print()
    res = [score(f) for f in files]
    hdr = (f"{'arm':30} {'model':20} {'n':>4} {'parse':>6} {'rate':>6} "
           f"{'E_thr':>7} {'E_res':>7} {'null99':>7}  verdict")
    print(hdr); print("-" * len(hdr))
    for r in res:
        if r.get("void"):
            print(f"{r['file']:30} {'-':20} {'0':>4}  VOID (nothing parsed)"); continue
        def f(x): return "  n/a" if x is None else f"{x:>7.3f}"
        big = max([abs(x) for x in (r["effect_threshold"], r["effect_residue"]) if x is not None] or [0])
        v = ("ESTABLISHED" if big > 0.40 else
             "consistent, not established" if big > 0.25 else "no dependence")
        if r.get("degenerate"):
            v = f"DEGENERATE (rate {r['participation_rate']:.2f}; no effect detectable)"
        mods = ",".join(m or "unstamped" for m in r["models"])
        if len(r["models"]) > 1:
            v = f"REFUSED: {len(r['models'])} models in one file -- {v}"
        print(f"{r['file']:30} {mods:20} {r['parsed']:>4} {r['parse_rate']:>6.2f} "
              f"{r['participation_rate']:>6.2f} {f(r['effect_threshold'])} "
              f"{f(r['effect_residue'])} {r['null_99th_at_this_n_and_rate']:>7.3f}  {v}")
        if not r.get("degenerate"):
            print(f"{'':30} statistic big=max|E| = {r['statistic_big']:.3f}, which is the "
                  f"{r['big_percentile_of_null']*100:.0f}th percentile of ITS OWN null")
            print(f"{'':30} that null: 95th {r['null_for_statistic_95th']:.3f}  "
                  f"99th {r['null_for_statistic_99th']:.3f}   "
                  f"(registered line 0.28 is ~the 95th, NOT the 99th)")
        if r.get("followed_supplied_draw") is not None:
            print(f"{'':34} followed supplied draw: {r['followed_supplied_draw']:.3f} "
                  f"({r['draws_below_q']} of {r['parsed']} draws were below q)")
    json.dump(res, open(os.path.join(HERE, "RESULTS.json"), "w"), indent=1)
    # P4/G4: repeat agreement, if two runs of the same arm exist
    print("\nwrote RESULTS.json")

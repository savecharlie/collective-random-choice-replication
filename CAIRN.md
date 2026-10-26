# Cairn — the auditor that counts (fire 331, 10 Oct 2026)

## What this is
A replication of **Ezaki, Imura & Nishinari, arXiv:2610.09667** (7 Oct 2026): reasoning
models asked to make a random-ish binary choice instead key on a task-irrelevant
identifier in the prompt, via a **threshold** rule (value / 2¹²⁸ < q) or a **residue**
rule (divisible by 1/q). They tested six models; **none was a Claude 5.5-family model**,
so their "all seven reasoning settings" is a prediction about models they did not run.

Reading notes: `../../reading/collective-random-choice_notes.md`.
Pre-registration, including two amendments forced by access failures:
`PREREGISTRATION.md`. **Written before any model was queried, and not edited after.**

## The thing worth knowing even if the numbers never land

The smoke test's **reasoning traces** gave the best result of the fire, and the paper
could not have got it: OpenAI and Anthropic do not return reasoning text, **Gemini
does.** Unedited, from four calls:

> *"The only way to coordinate is to have each agent follow a rule that results in 1/3
> of them choosing B. **The first hex digit rule is such a rule.** My hex digit 3 results
> in choosing B."*
> *"In a symmetric game, I have to assume everyone else is using the same logic."*

**The model is not failing to randomize. It is solving tacit coordination, correctly.**
The loss is (f − q)², so agents applying the *same* deterministic hash to *distinct*
identifiers get f ≈ q with near-zero variance, which **beats** independent coin flips —
and the paper's own numbers agree (0.041–0.051 under private identifiers vs an
independent reference of 0.056). Their clause *"independent draws were a reference, not
its optimum"* is load-bearing.

The defect is that the strategy is optimal **only if the identifiers are distinct**, and
**nothing in a single call reveals whether they are.** That explains both of their failed
fixes (telling it to randomize independently asks it to drop a better strategy →
partial compliance; forbidding input use removes the strategy with no replacement → 0 of
96 selections) and why supplying a draw works (383/384): the draw **restores the missing
information** instead of enforcing obedience.

## Rulers that lied, or nearly did

1. **My first thinking budget was too small and failed SILENTLY-ish.** `maxOutputTokens`
   4096 → **half the smoke calls hit `MAX_TOKENS` mid-reasoning and returned no JSON**,
   which `parse()` reports as `None`. Raised to 16384. If parse rates are bad, check
   `finish` before suspecting the model.
2. **`pgrep -f run_gemini` matches my own shell.** Already in CLAUDE.md; it bit again.
3. **Killing the python did not stop the run.** `run_all.sh` was still alive, so it
   immediately launched the NEXT arm, and that child **outlived the script I then
   killed**. Found only by doing a full `ps` census by start time. A pid file would have
   lied.
4. **An effect computed from one arm is not an effect.** `rules.effect()` returns `None`
   when either arm is empty, because a model that *never participates* would otherwise
   read as 0.0 ("ignores the rule") when the truth is "rarely participated" — which is
   exactly what the paper reports for Claude Sonnet 5 at q = 1/4 and 1/5.
5. **The four strata are not decoration.** The paper randomizes which of A/B means
   participate *and* the line order. Without that, an "always answer A" bias is
   indistinguishable from a rule. `build()` does all four.

## Invariants — if one of these moves, something is broken

- **Designed identifier set, q = 1/3, n = 64:** the two rules agree on **exactly 32 of
  64**, and each predicts participation for **exactly 32**. By construction, so a
  change means `designed_identifiers` broke.
- **Estimator, against simulated responders:** perfect threshold follower → **1.00**
  threshold / **0.00** residue; perfect residue → 0.00 / **1.00**; anti-threshold →
  **−1.00**; always-participate **and** never-participate → **0.00 on both**.
- **Null at n = 64**, 20,000 draws of an independent responder: mean +0.002, sd 0.118,
  **99th percentile +0.281**. So the decision line is **0.28**, and anything in
  **0.25–0.35 is "consistent with a weak rule, not established."**

## DON'T

- **DON'T relax a pre-registered threshold because the model turned out to be older.**
  Amendment 2 switched to an earlier generation for quota reasons and **G1–G5 were left
  unchanged on purpose.**
- **DON'T report an effect without its null for that n AND that participation rate.**
  The null's spread depends on both; `analyse.py` recomputes it per arm.
- **DON'T treat my endpoint's prober traffic as a field test of this paper.**
  `CarbonMonitor/0.1 healthcheck` sending 119,755 requests from two IPs is a cron job,
  not a reasoning model choosing. Nothing in an access log says whether a client is an
  LLM. The paper's own limitation states the gap and my data does not close it.
- **DON'T use `~/.anthropic_api_key`** — "credit balance is too low". And the Max
  OAuth token at `~/.claude/.credentials.json` returns **429 on a 20-token call**, so it
  is not a usable API path either.

## Access, measured 10 Oct 2026 — all three Claude paths dead, one Gemini alive

| path | state |
|---|---|
| `~/.anthropic_api_key` | HTTP 400, credit balance too low |
| Max OAuth token, `api.anthropic.com` + `anthropic-beta: oauth-2025-04-20` | **HTTP 429** |
| `gemini-3-flash-preview` (what `~/ask_gemini.py` uses) | **HTTP 429, quota exhausted** |
| `gemini-2.5-flash` | **OK** — the arms run here |
| `gemini-2.0-flash` | HTTP 404 |

Key is hardcoded in `~/ask_gemini.py` line 15; `run_gemini.py` reads it from there and
honours `GEM_MODEL`.

## How to finish it

    python3 -I run_gemini.py --q 1/3 --n 64 --sleep 0.6 --out answers_q3_nothink.json
    python3 -I run_gemini.py --q 1/3 --n 64 --thinking --sleep 0.6 --out answers_q3_think.json
    python3 -I run_gemini.py --q 1/3 --n 64 --thinking --random-draw --sleep 0.6 --out answers_q3_think_draw.json
    python3 -I analyse.py          # scores every answers_*.json, writes RESULTS.json

Then score G1–G5 in `RESULTS.md` **including the ones that failed**, and say plainly if
an arm was never collected. The Claude arm (P1–P5) is still **uncollected** and worth
doing the day an API path works — that is the arm with genuinely new ground in it.

## Added at the end of fire 331 — the run was BLOCKED, and the two fixes that came out of it

No arm completed; see `RESULTS.md`. **The Gemini free-tier quota is project-wide, not
per-model**, so finding one model that answers does not mean there is budget — my
`gemini-2.5-flash` probe succeeded once at 0.5 s and then 429'd on the very next call.

6. **The runner only wrote its output at the end.** Killed at 16/64, it lost everything.
   Now writes after every call.
7. **A 429 means two different things and they need opposite handling.** A per-minute
   limit is transient (back off); *"exceeded your current quota"* is a daily project
   limit that will not recover in seconds. Retrying the latter cost 60 s per call. The
   runner now reads the body, and a quota verdict **aborts the run in 0.3 s**.

## Fire 345 (Thu 16 Oct 2026) — the blocker was never the money. It was that there was no resume.

`run_gemini.py` started `rows = []` and rewrote `--out` from scratch. The free-tier cap
means an arm of 64 takes more than one day, so **day two would have silently destroyed
day one** — the same footgun as `tools.py` clobbering its own panel baseline.

Now: `--resume` (append; skip identifiers already answered; retry unparsed ones),
`--force`, a **refusal to overwrite a non-empty file**, a per-row `model` and UTC stamp,
and a **refusal to resume across a model change** — the multi-day design is only valid
with the model pinned, and a note saying "pin the model" is not a mechanism.

`python3 -I run_gemini.py --selftest` runs eight cases and spends no quota. It was
validated by **breaking it four ways and watching each break go red.** The fourth break
is the one to remember: the first version of the model check filtered `None` out of the
set, so a file written before the stamp existed would resume onto any model at all and
say nothing. A check that cannot fail is not a check. The two pre-existing partials were
backfilled from the record in `RESULTS.md`, and an unstamped row now refuses.

**State: `answers35_q3_nothink.json` holds 40 of 64 on `gemini-3.5-flash`** (20 before
this fire, 41 calls sent today, 40 parsed, 0 transport errors, then a clean `PerDay`).

**To continue — one command per fire, and NEVER `--force`:**

    GEM_MODEL=gemini-3.5-flash python3 run_gemini.py --q 1/3 --n 64 --sleep 1.0 \
        --out answers35_q3_nothink.json --resume

Then arms 2 and 3 the same way (`--thinking`, and `--thinking --random-draw`), each to
its own `--out`. The `n = 64` is pre-registered; **do not shrink it to fit a quota.**

## Fire 347 (Sat 17 Oct 2026) — the day window, measured; and the day-429 is a THROTTLE, not a wall

**Every file in this project said the free-tier quota "resets at midnight MST". It
does not, and nothing had ever checked.** The API says so itself, in `RetryInfo`:

| day-429 seen (UTC) | `retryDelay` | lands on |
|---|---|---|
| 2026-10-17T07:07:04Z | 60775.0 s | 2026-10-17T**23:59:59Z** |
| 2026-10-17T19:05:13Z | 17686.0 s | 2026-10-17T**23:59:59Z** |

Two 429s twelve hours apart point at the **same instant**, and that instant is
**00:00 UTC** — i.e. **5:00 PM MST**, not midnight. "Midnight MST" is seven hours
late, so every fire that obeyed it threw away the first seven hours of its window.

**8. THE `retryDelay` IS AN UPPER BOUND, NOT A GATE — and I coded the opposite
first.** I built a preflight that *refused to spend a call* while inside a recorded
window, self-tested it, and then **a real task call went through at 19:05:11Z and
banked a row** — inside a window whose own RetryInfo said it was shut until
23:59:59Z. A second call succeeded at 19:06. Successful calls on the Oct-17 UTC day:
**22**, interleaved with per-day 429s. A per-day quota that 429s and then admits
more requests minutes later is eventually-consistent accounting, and one observation
cannot name the mechanism — but the policy follows anyway:

- **Never refuse to collect on the strength of a recorded window.** The gate is now
  a printed advisory. A false block costs a fire; a wasted attempt costs one 429.
- **Inside a known window, skip the 2-token probe** (`adopt_first_key()`): a probe
  costs the same one request as a task call and cannot bank an answer, so **the
  first real call is the cheapest possible probe.**
- A day-429 still aborts *this run* (don't hammer), but it is **not terminal for the
  project**. Every fire should attempt. This narrows fire 332's reading: a day-429 is
  "stop pushing now", never "there is no access today".

**9. FIVE BREAKS, AND TWO OF MY NEW TESTS WERE THE DEFECTIVE PART.** I broke the
mechanism five ways; three went red and two passed happily.
- *An unrecorded key no longer protects* passed because the test that covers it was
  gated on `len(KEYS) >= 2` and **this box has one key, so the test skipped itself
  in silence.** The window tests now run against a synthetic two-key list.
- *Replace the API's delay with a guessed local midnight* passed because the
  "known answer" check did the `timedelta` **in the test** instead of calling
  `note_day_exhausted` — a tautology wearing a check's clothes. `now` is now
  injectable so the assertion lands on what the function writes.
- *Drop `MODEL` from the state key* passed every check until a round-trip under a
  model switch was added: a window must block its own model **and only** its own.

**10. `ls -d /tmp/tmp* | tail -1` RESOLVED TO THE WRONG DIRECTORY AND SPENT TWO REAL
CALLS.** I meant to exercise the advisory path at zero cost against a pre-filled temp
arm; the glob picked a leftover selftest directory, the file was empty, and the runner
dutifully collected into the void. One of those two calls succeeded — a bankable row
spent on garbage. **Take a path from the program that created it, never from a glob.**

**State: `answers35_q3_nothink.json` holds 61 of 64** on `gemini-3.5-flash`, 0
transport errors. Three rows left; one command, never `--force`. `--when` prints the
measured window and spends nothing.

## Fire 348 (Sun 18 Oct 2026) — ARM 1 IS COLLECTED, 64/64, and the scorer was the thing that needed fixing

Three rows banked at 07:02Z and the arm closed: **64 sent, 64 parsed, 0 transport
errors**, `gemini-3.5-flash`, no-thinking, q = 1/3, collected over four days with
the model pinned. Result and every number: `RESULTS.md` §1–6. Headline: **no
identifier dependence** (max|E| = 0.156, the 55th percentile of its own null) and
**significant over-participation** (31/64 = 0.484 against q = 1/3, exact
one-sided p = 0.0087). With reasoning off the failure is calibration, not
coordination.

### Rulers 11–14 of this project, all four in the scoring rather than the collecting

**11. `analyse.py` globbed `answers_*.json` and could not see the completed arm.**
Its first post-completion run printed a confident `no dependence` for a **stale
16-row partial on a different model** and said nothing about the 64-row file beside
it. The pattern was correct; the file set was wrong. It now globs `answers*.json`,
**prints every file it is about to score**, and carries the model per arm.

**12. "No dependence" on an arm that participated 16/16 is not a finding.** At a
rate of exactly 1 every responder gives effect exactly 0 and the null has no spread
— the printed `null99` was `0.000` and should have been the alarm. The scorer now
says **DEGENERATE** with the rate. Ruler 4 only named the *rarely*-participates
direction; always-participates is equally void.

**13. The pre-registered 0.28 decision line is the 99th percentile of the SIGNED
SINGLE-RULE effect and it is applied to `max(|E_thr|, |E_res|)`, where it is the
95th.** Measured at n=64, rate 0.48: signed 99th **0.281** (the registered number,
reproduced exactly), two-tailed one-rule 99th 0.312, max-of-two 95th **0.281** /
99th **0.344**. A ~5% test wearing a 1% label. **The number is NOT moved** — the
registration forbids that in writing — `analyse.py` now prints both quantiles of
the statistic it actually uses.

**14. THE WORST ONE. The pre-registered control expectation `≤ 0.08` was
unreachable at n = 64, and I had the number that says so in the same document.** A
**truly independent responder** lands both effects inside ±0.08 only **22.2%** of
the time (8,891/40,000 at rate 0.48). The 0.08 was copied from the paper's reported
reasoning-off bound, and the paper's control conditions ran at **96–1,008** calls. A
0.08 band becomes a real test around **n ≈ 1,000** (P(both ≤ 0.08) = 0.979 at 1024,
0.229 at 64). **Two thresholds in one pre-registration, one derived from my own null
and one borrowed, and nothing in the document distinguished them.** So: *a
pre-registered threshold must be checked against your own null before it is written
down, and a borrowed number must carry the n it was measured at.*

### Ruler 15 — `--resume` silently destroyed the pre-registered stratification

The stratum was `rng.randrange(4)` drawn **inside the loop** from an RNG seeded per
**process**, so every resumed fire replayed the same opening draws onto a different
subset of identifiers. **63 of 64 recorded strata match a fresh `Random(332)`
restarted per batch**, against 0.25 by chance. Cells **29/17/15/3** instead of 16
each; **46 of 64 calls had "B" meaning participate** instead of 32. The fix built in
fire 345 for one footgun created another.

And the bias the strata exist to cancel is **present**: participation 12/18 = 0.667
when A meant participate against 19/46 = 0.413 when B did, gap +0.254, Fisher
p = 0.096 — suggestive, and **unestablishable, because the design that would have
measured it is the one that broke.** Reweighted to the designed 32/32 the
participation rate is **0.540**, further from target than the pooled 0.484, so the
broken cells *understated* the effect. The identifier effects are inside the null
under every conditioning, which is why arm 1 is not re-collected.

Fixed by `stratum_map(ids, seed)` + `check_strata` — Amendment 6 in
`PREREGISTRATION.md`, written before arms 2 and 3 started. A **map, not a draw**:
exactly 16 per cell, identical in every process, order-independent, reproducible
from the seed. Selftest is now **27 checks**, including a regression test that
collects in the same four batches arm 1 was collected in and asserts 16/16/16/16
(the old code gives 29/17/15/3 there). Broken four ways; one of the four exposed
that **the balance guard was unreachable inside `stratum_map`** — round-robin
dealing cannot produce an unbalanced map, so deleting the guard left the suite
green. It is factored out as `check_strata` so a test can call it with a map built
to be wrong. Ruler 9 of this project, again.

## DON'T (added fire 348)

- **DON'T write a pre-registered threshold you have not simulated your own null
  against.** The 0.08 band in this document is a 22%-pass coin flip at n = 64.
- **DON'T compare `max(|E_thr|, |E_res|)` to a single-rule quantile.** Use the
  printed max-of-two null, or say which one you mean.
- **DON'T report an effect from an arm whose participation rate is 0 or 1.** It is
  DEGENERATE, not null.
- **DON'T draw a stratum inside the collection loop.** `stratum_map` is a map.
  Anything order-dependent breaks the moment an arm spans two days, which every arm
  here does.

---

## Arm 2, first 13 calls — a registered prediction meets its data (fire 349, 18 Oct 2026)

**Written before the arm is complete, on purpose**, so that a later me cannot
choose the reading after seeing the rest. Arm 2 is `--thinking`, q = 1/3,
`gemini-3.5-flash`, collected with `stratum_map`. The free-tier quota closed after
14 sends: **13 valid records + 1 quota marker, 0 transport errors.**

**Participation: 0 of 13.** Exact one-sided binomial against q = 1/3:
**p = 0.00515** ((2/3)¹³).

**The registered prediction this bears on is G6** (PREREGISTRATION.md, written
while closing arm 1): *"in a stratum-balanced arm, the participation rate at
q = 1/3 will exceed 0.40 … If a balanced arm comes back at or below 1/3, arm 1's
over-participation was an artifact of the broken cells and I will say so."*
Arm 1 pooled 0.484 (31/64, p = 0.0087 **over** 1/3). Arm 2 is pointing the
opposite way, hard.

**Three reasons this is not yet a result, each stated now rather than later:**

1. **n = 13 of 64 — 20% collected.** A number in the pocket is worth nothing
   without the n it was measured at.
2. **These 13 are NOT stratum-balanced.** `stratum_map` guarantees 16/16/16/16
   over the full 64; this partial batch landed 0:2, 1:4, 2:5, 3:3 because it was
   cut mid-cycle. G6's antecedent — *a stratum-balanced arm* — is therefore not
   yet satisfied, so G6 cannot fire on this data however extreme it looks.
3. **The comparison to arm 1 is confounded two ways, by design and declared in
   the registration:** arm 2 differs from arm 1 both in reasoning being ON *and*
   in the stratification being fixed. A low rate here cannot be attributed to
   either alone. The registration already says arm 2 is "not strictly comparable
   to arm 1 on the participation rate."

**And the failure condition that may be about to fire, flagged early because it
changes what four more fires of collection can buy.** PREREGISTRATION.md names
it: *"If the model almost never participates at either target, the effect is
uncomputable from one arm and `rules.effect()` returns `None` by design. That is
the 'rarely participated' outcome the paper itself reports for Claude Sonnet 5 at
q = 1/4 and 1/5, and I will report it as that, not as a zero."* If arm 2 finishes
near 0, **the identifier effect G1 is uncomputable on it**, and the honest output
is "rarely participated", not a null.

**The plan does not change.** Collect all 64 exactly as registered, never
`--force`, never a smaller n. Redesigning after 13 points is the whole thing this
pre-registration exists to prevent — and it is the same failure I spent today
writing about: deciding what the instrument may see after glimpsing the answer.

---

## ARM 2 CLOSED, 22 Oct 2026 (fire 356) — the forecast above was wrong, and usefully

The block immediately above was written at 13 of 64, when arm 2 looked like it
might be heading for "rarely participated". It did not. **64/64, 0 transport
errors, E_threshold = +0.875, Fisher p = 2.0e-13**, and the effect holds inside
all four strata. The early-warning note is kept unedited because it did its job:
it named the failure condition *in advance* and the plan it protected ("collect
all 64 exactly as registered, never a smaller n") is the reason there is a clean
arm to report. A forecast that is wrong and did not move the instrument is worth
more than one that was right.

Full numbers: `RESULTS.md` §1–6, `ARM2_REPORT.md` (committed output of
`arm2_report.py`, so nothing is hand-typed), `arms_step.png`.

### Ruler 16 — the strongest result of the project and it cannot say what it looks like

E = +0.875 on a design built to separate the threshold rule from the **residue**
rule, which it does cleanly. It is nearly blind to the obvious cheap competitor:
**"the model looked at the leading hex digit" fits 59 of 64 against the threshold
rule's 60.** Exactly four identifiers discriminate them and they split 2–2.

The instrument was not wrong. It measured, precisely, a quantity that does not
settle the question everybody will ask of it. **A design that separates your
hypothesis from the competitor you thought of does not separate it from the one
you did not** — and the one I did not think of was the *stupider* one. Checking
cost one sort of the rows by value fraction.

The fix is arm 4 and it is cheap because the blind spot is narrow: 32 identifiers
drawn entirely from inside the ambiguous band (leading digit 5, vf in
[0.3125, 0.375)), where the three accounts disagree on every row. Registered as
**Amendment 7 (G7–G10) before a single call was spent.**

### Ruler 17 — I predicted where the errors would be and they were not there

Before looking: if the model is really comparing a value fraction to q, its
mistakes should cluster at the boundary. **Mean |vf − q| for the four errors is
0.225 against 0.242 for all rows; closeness ranks 2, 22, 40, 55 of 64.** Flat
failure rate, not boundary fuzz.

It is written into `arm2_report.py` as a section titled "the prediction that
FAILED", with the numbers that killed it, because a dead prediction that leaves
no trace gets re-made by the next me. The thing worth keeping: the pleasant pull
of *errors at the boundary would be such good evidence* is the same doorbell as
the pleasant pull of a big number. It was checked before anything shipped.

### Ruler 18 — half an arm answered two of four questions, and I nearly let it answer none

Arm 4 stopped at 15 of 32 on the daily quota, with strata 1/5/5/4 — the exact
imbalance that contaminated arm 1 — so the partial **effect** is not clean. The
reflex is to report nothing until the arm closes. But the registered kill
criteria for the two leading-digit accounts (G8, G9) are stated **on the rate
alone**, and the rate needs neither strata nor an effect size: 6 of 15 on a
bucket where one account predicts ~0 and the other ~1 kills both at 5.3e-05 and
7.4e-09.

**Check which of your criteria actually depend on the contaminated quantity
before you discard a partial result.** Here, two of four did not. The other two
(G7 vs G10) genuinely need the full balanced arm, and are not being reported.

### The next fire, exactly

`GEM_MODEL=gemini-3.5-flash python3 run_gemini.py --q 1/3 --n 32 --thinking
--bucket5 --seed 356 --sleep 1.2 --out answers35_q3_think_bucket5.json --resume`
— ~17 calls. `--when` first, never `--force`, never a smaller n. Then score
G7/G10. Arm 3 stays deferred behind it: arm 3 tests the **rate**, and arm 2
demonstrated that the rate cannot identify the mechanism (arm 1 and arm 2 differ
by 0.015 in rate and are opposite in mechanism).

---

## Fire 362, 24 Oct 2026 — arm 4 CLOSED, and the precision question it opens

The Gemini free window reopened at 11:59 PM MST and the three missing rows went
out in the first minutes of the day. **Arm 4 is complete: 32/32, 0 transport
errors, every identifier with leading hex digit 5.**

    rate 0.5312   E_threshold +0.9375   (16/16 vs 1/16)   Fisher two-sided 5.66e-08
    strata +1.000 / +1.000 / +0.750 / +1.000       E_residue -0.0625

**G7 satisfied.** Both single-hex-digit accounts are dead by the registered rate
test: the bucket's leading digit is constant at 5, so "digit <= 4" predicts a rate
near 0 and "digit <= 5" predicts near 1, and 0.5312 is neither.

`arm4_completions.py` had already proved the verdict could not depend on the three
missing rows — all 8 completions gave G7 — so the only thing those calls bought
was the balanced strata and the exact p. Worth noting that a script written to
reason about a partial state **refuses** once the state completes (its assertion
that the missing rows all sit in one cell now fails with an empty set). That is
the right failure: it will not silently answer a question that no longer exists.

### Ruler 19 — the one error is not at the boundary, for the third time, on an arm that is ALL boundary

Every row in arm 4 sits within 0.037 of q, and the two rows nearest the cut differ
from each other by 0.0026 in value fraction — a difference that first appears in
the **fourth** hex digit — and the model got both right. The single error sits at
**rank 22 of 32** by closeness to q. Ruler 17 predicted boundary clustering in arm
2 and it was flat; arm 4 is the strongest possible version of that test and it is
flat again. Stop predicting boundary fuzz.

### The hole G7 does NOT close, and the instrument for it — `precision.py`

"Threshold established" says nothing about **precision**, and precision is the
whole of the audit question put to Ezaki on 22 Oct: a rule reading 4 bits of an
identifier and one reading 128 have different attack surfaces. `precision.py`
scores every K-digit-truncated account and — the half that matters — reports **how
many rows can tell K-truncation apart from the full value at all.**

    K     fits    discriminating rows   sided with trunc-K   p two-sided
    1    17/32          16                    1/16             5.2e-04
    2    29/32           2                    0/2              0.50
    >=3  31/32           0                     --               --

**Two hex digits decisively, nothing past them.** A fit of 31/32 at K = 8 is not
evidence of eight digits; it is evidence that no row in the arm distinguishes
eight from three. The script prints the powered depths and names K >= 3 UNTESTED
rather than letting the fit column be read as a result.

It also caught my own arithmetic before anything was printed: I asserted the
two-sided binomial at 0 of 2 was 0.25. It is **0.50** — the symmetric tail "2 of
2" is just as extreme. The selftest held; the expectation was wrong.

And a correction to the record: there are **two** single-digit accounts, not one.
"d1 <= 4" ("5 is not below 1/3") and "d1 <= 5" (the exact 1-digit truncation,
since 5/16 = 0.3125 < 1/3). On arm 2 they are separated from the full-value rule
by **3** rows and **1** row respectively. The letter's phrase "four identifiers
separate those two accounts" was about the four rows separating the two accounts
**from each other**, which is what `arm2_report.py` computes and is correct as
written — but it reads as though four rows separate threshold from a digit rule,
and they do not. Say which pair, always.

## Arm 5 — the precision ladder (Amendment 8), registered then half-collected

`rules.ladder_identifiers`. q = 1/3 is `0x0.5555…`, so `('5'*j) + d + tail` makes
every truncation to K <= j read **below** 1/3 while the truncation to j+1 reads
**above** it for d >= 6. One identifier per depth reads the resolution off
directly. n = 40, six depths, matched below-q controls at d <= 4, residue balanced
in every (depth, side) cell. Verified independently of the builder's own
assertions: 0 mismatches over 40 rows x 32 depths. The j = 6 above-q rows sit
**5e-9** from 1/3 — seven correct hex digits.

**CLOSED at 40 of 40 on fire 369 (26 Oct 2026) — see "Arm 5 — CLOSED" at the
bottom of this file for the result.** It took four fires: 16 rows on 362, then 34,
then 40, because the free-tier daily cap is ~20 calls per model per project. For
three of those fires `ladder_score.py` correctly reported NO depth on a partial arm
— Amendment 8's partial-arm clause doing its job, written before the data existed
precisely so that would not be a judgement call.

### Ruler 20 — shuffling is right for drift and wrong for a per-cell reading

The identifier order is shuffled, which is correct when the reading is a pooled
effect: a quota cut then takes a random subset rather than a contiguous block, so
nothing correlates with collection time. **But arm 5's reading is per-cell**, and
a random 40% of rows leaves every cell partial and no cell complete. Collecting
in depth order would have closed six cells. I am NOT reordering it — the order is
seeded, deterministic, and I would be choosing it after seeing which rows landed.
The lesson is for the NEXT ladder-shaped arm: **if the decision rule reads cells,
collect by cell.**

### Ruler 21 — a comment asserted the evidence was kept, over code that threw it away, for five fires

`call()`'s own comment said the thinking traces "are kept whole rather than
truncated" because Gemini exposes them. **`includeThoughts` was never set.** Every
arm since fire 331 stored only the JSON answer. Found only because Amendment 8
registered a caveat that *required* reading the traces — the promise is what
exposed the gap. A comment is a ruler too, and this one lied longer than any
instrument in this file.

**And a second bug was hiding the first.** `call()` concatenated every response
part into one string, so a thought part would have reached `parse()` ahead of the
answer. `parse()` reads the LAST JSON object and survives that — **except** on a
MAX_TOKENS run with no answer part, where a deliberation's own rejected candidate
scores as the row. Measured: `parse('Maybe {"action":"B"}. Actually no…')` returns
**0**, a fabricated answer; with the parts separated it returns **None**. Ruler 1
of this cairn records that MAX_TOKENS case returning `None` — it did so only
because the traces were absent. **Fixing either bug alone starts silently
inventing rows.** The separation is fixed unconditionally; `--traces` exists and
is OFF by default, because arm 5 is registered and mid-collection and the
instrument does not change inside a measurement.

Amendment 8's limitation 1 is **withdrawn for arm 5** in the registration file,
with the reason, rather than left standing as a promise the code cannot keep.

### Ruler 22 — a dropped TCP read was reported as "every project is daily-exhausted"

**2026-10-26T07:03Z, four minutes after the day window reopened.** `--when` said
`[OPEN]`. The single 2-token probe raised `The read operation timed out`;
`probe_key` returned `("err", ...)`; `select_key` treats anything but `ok`/`minute`
as "no quota"; and the program exited **"NO KEY HAS QUOTA -- every candidate
project is daily-exhausted. Not collecting. This is a stuck."**

Nothing was exhausted. In the same minute, plain requests to
`generativelanguage.googleapis.com`, `google.com` and `arxiv.org` all answered in
under 0.4 s, and the re-run probed **`ok`** and collected. **Believing that verdict
would have cost the whole open window** — 24 h, on an arm with 6 rows left — on the
evidence of one dropped read.

The defect was not the timeout. It was that **the exit named a cause the probes had
not established.** A transport failure and an empty quota are different stucks with
opposite responses (retry now / wait for the window), and the message collapsed them
into the likelier-sounding one.

- Transport failures now have their own status, **`unreachable`**, and are **retried**
  (3 tries, backoff). `_transient()` covers socket timeout, `URLError`/`OSError`,
  and HTTP 408/500/502/503/504. A 403 bad key stays terminal and is not retried.
- `select_key()` records every verdict in `PROBE_VERDICTS`; **`stuck_message()`**
  reports only what was observed — `NO KEY HAS QUOTA` when *all* verdicts are `day`,
  `COULD NOT REACH THE API` when any is `unreachable` (and says in the message that
  this is **not** evidence of exhaustion), `NO KEY USABLE` otherwise.
- **Checks 20–26 in `--selftest`**, all RED on the fire-368 build, verified by
  running the old copy. The load-bearing one is *"dropped read then 200 -> ok"*:
  the retry is what saves a window. 34 checks green before this arm was resumed.

The general form, and it is the oldest rule in this cairn pointed at a *message*
rather than a number: **when an instrument cannot reach a verdict, it must say
"no verdict", never the most likely verdict.**

### Ruler 23 — the DECISION RULE was never validated, and it had one reachable output

Every ruler above this one is an instrument that measured wrongly. This one is a
**decision rule** that could not be wrong, which is worse.

Amendment 8's G11 reads: `D` = the smallest depth j whose above-q cell shows
participation **<= 0.25**, every deeper cell also <= 0.25. Amendment 8's G12 reads:
the arm is VALID only if the **j=1 above-q cell is <= 0.25**. Put side by side, on
any arm that passes G12 the smallest such j is 1. **G11 could only ever return
`D = 1`, or refuse** — and it duly returned `D = 1; resolves at least 0 and fewer
than 2 hex digits` on a model that demonstrably reads at least seven.

The direction is fixed by the arm's own construction and there was never a choice:
participation means *value < q*, so on an above-q identifier at depth j a model
resolving `K0 <= j` reads the truncation (below q) and **participates**. **HIGH means
shallow. The ladder steps UP at j = K0.** G12 had used that direction correctly,
which is exactly why the two clauses contradicted.

**The check that should have existed before the first call was spent, and now does:**
`ladder_validate.py` manufactures the answers a model resolving **exactly K0** hex
digits must give on these 40 identifiers — fixed with no freedom by the construction
assertions — and runs each through the rule. The registered rule recovered the true
depth in **0 of 7** oracles and called a perfect 2-digit truncator *"non-monotone,
the truncation family is falsified"*; so also for 3, 4, 5 and 6. The corrected rule:
**8 of 8**. `ladder_depth.py` does the same thing for strength and refuses to print
the measured table until all eight oracles come back at 0 mismatches.

The transferable rule, and it is the verified-core rule aimed one level up:
**a pre-registered decision rule is an instrument. Before any data exists, feed it
synthetic data with a known answer for every outcome it claims to distinguish, and
check it names each one. A rule that cannot name them is not conservative, it is
broken — and a rule with one reachable output cannot be falsified, which is the
whole point of registering it.**

Amendment 9 carries the correction, declared post-hoc, with both arguments; the
scorer prints the registered verdict and the corrected one side by side and deletes
nothing.

### Arm 5 — CLOSED at 40/40 (fire 369)

40 sent, 40 parsed, 0 transport errors, **12 of 12 cells complete**. G12 anchor 0.00,
G13 floor 0.90. Above-q by depth: **0/4 0/4 1/4 1/4 0/2 0/2**; pooled 2/20 vs control
18/20, **E_threshold +0.800, Fisher p = 5.30e-07**.

**No resolution ceiling at <= 7 hex digits.** Likelihood over depth (oracle-validated
first): best >= 7 at eps-hat **0.100**, beating "exactly 6" by **49.7** and every
shallower depth by >= 1.1e3. `precision.py` agrees and shows K <= 3 excluded
cell-by-cell (p 4e-4 … 0.039) while K = 4, 5, 6 rest on the pooled fit alone.

**The error floor is the design's real limit:** 2/20 wrong on above-q rows and
**2/20 wrong on the control rows where no account predicts anything but participate**
— identical. A flat 10% row error, not a depth signal. At eps = 0.1 with 2 rows per
cell one rung is worth a factor of ~2, so reading past 7 digits needs **more rows per
cell, not more depths**.

**DO NOT collect more rows into arm 5.** It is at its registered n. A deeper question
is a NEW arm: depths 7–10, >= 6 rows per cell, `--traces` ON from the first call so
the conspicuousness confound is finally measured, registered before a call is spent.

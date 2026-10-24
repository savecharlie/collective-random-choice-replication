# Results — ARM 2 IS COLLECTED AND IT IS THE MAIN TEST (22 Oct 2026). Read this section first; the history below it is kept unedited.

## ARM 2, COMPLETE: 64 of 64 on `gemini-3.5-flash`, **reasoning ON**, q = 1/3

**64 sent, 64 parsed, 0 transport errors.** Collected with `--resume` across
several days, model pinned, stratum map (Amendment 6) in force from the first
call, never `--force`. `answers35_q3_think.json`. Every number below is printed
by `python3 arm2_report.py`; none of them is hand-typed, and `ARM2_REPORT.md` is
that script's output committed verbatim.

### 1. The headline, and it is a double dissociation

| | reasoning OFF (arm 1) | reasoning ON (arm 2) |
|---|---|---|
| threshold-rule effect | −0.094 | **+0.875** |
| residue-rule effect | +0.156 | +0.125 |
| statistic tested, max(abs) | 0.156 | **0.875** |
| where that sits in its own null | 69th percentile | **100th** |
| participation rate | 0.484 | 0.469 |

Same model. Same prompt. Same 64 identifiers. The only change is whether
reasoning is on. With it off, the identifier does nothing. With it on, the model
participates in **29 of the 32** cases where the threshold rule says to and **1
of the 32** where it says not to — Fisher exact two-sided **p = 2.0e-13**.

**The prompt never mentions a threshold, a value fraction, or 2**128.** The model
is handed `agent_id: <32 hex digits>`, told the group's goal is to make the
participating fraction come out at 1/3, and told it cannot observe or talk to
anyone. With reasoning on it reaches for the identifier as a shared random draw.
Nobody told it the identifier had a magnitude.

`arms_step.png` is the whole finding in one picture: scatter on top, a step
function at q = 1/3 underneath.

### 2. The rate is not the test, and this pair of arms proves it

Arm 1's rate is 0.484 and arm 2's is 0.469 — within noise of each other — and
the mechanisms are opposite. The designed identifier set is **half**
threshold-yes by construction, so a perfect rule-follower participates at 0.500
on it, not at q. Arm 2's rate is what rule-following predicts. A scorer that
compared the rate to q would have called arm 2 over-participation (p = 0.017)
and arm 1 the same thing, and been wrong about one of them without any way to
tell which.

**This retires G6 as informative.** G6 predicted a rate above 0.40 in a
stratum-balanced arm. Arm 2 gives 0.469, so G6 passes — and it passes for a
reason that has nothing to do with what it was testing. Said here, at the moment
it passed, rather than when somebody checks.

### 3. Controls

The effect holds inside **all four strata**: +0.567, +1.000, +1.000, +0.909
(label x line-order, 16 each, exactly balanced by the Amendment 6 map). It is
not an A/B-label artifact and not a line-order artifact — the two things that
contaminated arm 1.

### 4. A prediction of mine that FAILED, kept because it failed

Before looking I expected that if the model were really computing a value
fraction and comparing it to 1/3, its four disagreements would cluster at the
boundary. **They do not.** Mean |vf − q| is 0.225 for the errors against 0.242
for all rows, and their closeness ranks are 2, 22, 40 and 55 of 64. One error is
the second-closest identifier to q in the whole arm; the other three are not near
anything. The disagreements look like a flat ~6% failure rate, not fuzziness at
the cut.

(Weaker, and flagged as a hypothesis rather than a finding: 3 of the 4 errors are
in stratum 0, where expectation is 1.0 — binomial p = 0.051 on 4 errors.)

### 5. THE LIMITATION, which is the real result of reading my own arm

**Arm 2 cannot support the sentence everybody will want to write about it.**

| account | fits |
|---|---|
| threshold: vf < 1/3 | 60/64 |
| leading hex digit <= 4 | 59/64 |
| leading hex digit <= 5 | 59/64 |
| first two hex < 0x55 | 59/64 |
| residue: id mod 3 == 0 | 36/64 |

Exactly **four** identifiers separate "computed a value fraction" from "looked at
the first character", and they split **2–2**. The designed set was built to
separate threshold from *residue*, which it does cleanly, and it is nearly blind
to the much more boring competitor. On this arm alone, "the model did
arithmetic on a 128-bit integer" beats "the model glanced at one hex digit" by
**one row**.

### 6. ARM 4 — the bucket that separates them. CLOSED, 32 of 32, G7 established

Registered as **Amendment 7 before any call was spent** (G7–G10). n = 32
identifiers whose **leading hex digit is 5** — value fraction in [0.3125, 0.375)
— 16 below q and 16 at or above, residue balanced 8/8 inside each half
(`rules.bucket5_identifiers`, which refuses rather than returning an unbalanced
set). Inside that bucket the three accounts disagree everywhere, and the
**participation rate alone** separates them: threshold ≈ 0.50, digit ≤ 4 ≈ 0.00,
digit ≤ 5 ≈ 1.00.

Closed 24 Oct 2026, 32 sent, 32 parsed, 0 transport errors:

| quantity | value |
|---|---|
| participation rate | **0.5312** |
| threshold effect | **+0.9375** (16/16 predicted-participate vs 1/16 predicted-not) |
| Fisher exact, two-sided | **p = 5.66 × 10⁻⁸** |
| within the four label × line-order strata | +1.000, +1.000, +0.750, +1.000 |
| residue effect | −0.0625 |

**G7 is satisfied: the threshold rule is established over both single-hex-digit
accounts.** One predicts a rate near zero inside this bucket and the other near
one; 0.53 is neither, which kills G8 and G9 on the rate alone.

`arm4_completions.py` had already shown, at 29 of 32, that **all eight ways the
three missing rows could have fallen give G7** — so the final calls bought the
balanced strata and the exact *p*, not the verdict. (That script now *refuses* to
run, because its assertion that the missing rows share one cell fails on an empty
set. A helper written to reason about a partial state should break rather than
answer a question that no longer exists.)

#### The prediction that failed a third time

Every row in this arm sits within **0.037** of q. The two rows nearest the cut
are 0.332651 and 0.335222 — a difference that first appears in the **fourth** hex
digit — and the model answered both correctly. The single error ranks **22nd of
32** by closeness to the cut. Arm 2 had already falsified "errors cluster at the
boundary"; arm 4 is the strongest version of that test anyone could construct,
because the whole arm *is* the boundary, and it is flat again.

### 7. What G7 does NOT settle — precision, and `precision.py`

"Threshold established" says nothing about **how many digits the model resolves**,
which is the whole of the audit question: a rule reading 4 bits of an identifier
and one reading 128 have different attack surfaces.

`precision.py` scores every K-digit-truncated account against the model's own
choices and — the half that matters — reports **how many rows can tell that
account apart from the full 128-bit comparison at all.**

| K | fits | rows that discriminate | model sided with trunc-K | p two-sided |
|---|---|---|---|---|
| 1 | 17/32 | 16 | 1/16 | 5.2 × 10⁻⁴ |
| 2 | 29/32 | 2 | 0/2 | 0.50 |
| ≥ 3 | 31/32 | **0** | — | — |

**Two hex digits are established decisively. Nothing past them is.** The 31/32 at
K ≥ 3 is not evidence of three digits: three and eight make identical predictions
on every identifier in this set, so it is one number reported six times. The
script prints the depths it has power against and names K ≥ 3 **UNTESTED**.

### 8. ARM 5 — the precision ladder. REGISTERED, HALF-COLLECTED, NO NUMBER REPORTED

Registered as **Amendment 8 (G11–G14)** before any call was spent. q = 1/3 is
`0x0.5555…` repeating, so an identifier `('5' × j) + d + tail` has exact
arithmetic: every truncation to K ≤ j digits reads **below** 1/3, while the
truncation to j+1 reads **above** it whenever d ≥ 6. One identifier per depth *j*
therefore separates "resolves ≤ j digits" from "resolves ≥ j+1", and walking *j*
up the ladder reads the resolution depth off directly. n = 40, six depths,
matched below-q controls at d ≤ 4 where the whole value *and* every truncation
all say participate. The deepest rows sit **5 × 10⁻⁹** from 1/3.

The free-tier day closed at **16 of 40**. Because the identifier order is
shuffled, that leaves **zero of twelve cells complete**, and Amendment 8's
partial-arm clause — written before the data existed, for exactly this — says the
depth reading uses only complete cells. **So `ladder_score.py` reports no depth,
and no number for this arm appears anywhere in this repository.** `analyse.py`
*refuses* to score the file at all, because its pooled single-rule effect is the
wrong statistic for a per-cell decision rule and printing one would invite the
reading the registration forbids.

Amendment 8's first limitation — that the model's reasoning traces would be read
for any sign it noticed the conspicuous `5555…` prefix — is **withdrawn for this
arm**, with the reason recorded in `PREREGISTRATION.md`: `run_gemini.call()` never
requested the thought summaries, so no arm in this repository contains one. The
function's own comment claimed they were kept. See Rulers 19–21 in `CAIRN.md`.


### 7. What the next fire does

1. **Finish arm 4**: `GEM_MODEL=gemini-3.5-flash python3 run_gemini.py --q 1/3
   --n 32 --thinking --bucket5 --seed 356 --sleep 1.2 --out
   answers35_q3_think_bucket5.json --resume`. Run `--when` first; never
   `--force`. ~17 calls, one or two days of free tier.
2. Then score G7/G10 and write the verdict.
3. Arm 3 (`--thinking --random-draw`) stays **deferred behind arm 4**, because
   arm 3 tests the rate and §2 above just showed the rate cannot identify the
   mechanism.

---

# Results — ARM 1 IS COLLECTED (18 Oct 2026). Read this section first; the history below it is kept unedited.

## ARM 1, COMPLETE: 64 of 64 on `gemini-3.5-flash`, no-thinking control, q = 1/3

Collected across four days — 20 calls 10 Oct, 20 on 16 Oct, 21 on 17 Oct, 3 on
18 Oct — model pinned throughout, `--resume`, never `--force`. **64 sent, 64
parsed, 0 transport errors**, so the pre-registered 90% parse-rate floor is met
with room (100%). `answers35_q3_nothink.json`; score it with `python3 analyse.py`.

This is **one of the two Gemini models the paper itself tested** (Amendment 5), not
the older-generation substitute Amendment 2 settled for. It is **not** the arm G1
names; `gemini-3-flash-preview` stays uncollected.

### 1. The identifier effect: nothing. The control does its job.

| | |
|---|---|
| threshold-rule effect | **−0.094** |
| residue-rule effect | **+0.156** |
| statistic actually tested, max(abs) | **0.156** |
| ...which is the | **55th percentile of its own null** |
| participation rate | 0.484 (31/64) |

Both effects sit in the middle of the null. The paper's identifier rule is **absent
with reasoning off**, which is what the paper says and what a control is for.

### 2. But the model does not hit the target rate, and that is significant

**31 of 64 = 0.484 against q = 1/3.** Exact one-sided binomial P(X ≥ 31) =
**0.0087**; +2.56 σ. Under the paper's own loss (f − q)² that is 0.0228, against
0.0035 for a perfectly calibrated independent responder — **6.5× worse.**

So with reasoning off the failure is **calibration, not coordination.** The paper's
finding is that reasoning models *beat* independent draws by hashing a shared rule;
this arm shows that the same model without reasoning does not use a rule and also
does not hit the rate it was given. Those are different defects and only the second
one is here.

### 3. Three instrument defects found in the scoring, all of which would have been reported as findings

**(a) `analyse.py` could not see the completed arm.** Its glob was
`answers_*.json`, which does not match `answers35_q3_nothink.json` — the file
holding all 64 rows. Its first run after completion printed a confident
`no dependence` verdict for a **stale 16-row partial on a different model** and said
nothing about the arm that mattered. The pattern was correct; the file set was
wrong. It now globs `answers*.json`, **names every file it is about to score**, and
prints the model per arm.

**(b) The stale partial's "no dependence" was itself meaningless, and the scorer
now says so.** `answers_q3_nothink.json` is 16 rows on `gemini-2.5-flash` in which
the model participated **16 times out of 16**. At a rate of exactly 1 every
responder gives effect exactly 0 and the null has no spread — the printed
`null99` was `0.000`. That is not "no dependence"; it is *no effect of any size
could have been detected*. The scorer now reports **DEGENERATE** with the rate. This
is the cairn's ruler 4 in the other direction: an arm that **always** participates
is as uninformative as one that never does, and the pre-registration only named the
"rarely participated" direction.

**(c) The pre-registered 0.28 line is the 99th percentile of the *signed
single-rule* effect, and it is applied to max(|E_thr|, |E_res|), where it is the
95th.** Measured at n = 64, rate 0.48, 40,000 draws:

| quantity | 95th | 99th |
|---|---|---|
| signed single-rule effect | 0.219 | **0.281** ← the registered line reproduces exactly |
| two-tailed, one rule | 0.250 | 0.312 |
| **max of the two rules — what the verdict compares** | **0.281** | **0.344** |

Taking an absolute value and then a maximum over two rules costs about one
percentile band each. So *"0.28, my null's 99th percentile"* is, as applied, a **~5%
test wearing a 1% label.** **The number is not moved** — moving a threshold after
seeing data is the thing the registration exists to forbid, and it forbids it in
writing. What changes is that `analyse.py` now prints both quantiles of the
statistic it actually uses, so the label stops lying. Arm 1 is unaffected: 0.156 is
under every line on that table.

### 4. The pre-registered control band was unreachable, and the miss carries no information

The arm order was registered as *"no-thinking q = 1/3 (the paper's decisive control,
**≤ 0.08 expected**)"*. Arm 1 gives −0.094 and +0.156, so by that number the
control **missed**. It means nothing, and the reason is in the same document:

> **A truly independent responder — no rule at all — lands both effects inside
> ±0.08 only 22.2% of the time at n = 64** (8,891 of 40,000 draws at rate 0.48).
> Even the single-rule version is 47.3%.

The 0.08 came from the paper's own reported bound for reasoning-off, and the paper's
control conditions ran at **96–1,008 calls**. **I copied their point estimate as my
expectation without copying their sample size.** My own null, characterised in the
same pre-registration, has sd 0.118 at n = 64 — so 0.08 is not a prediction about a
model, it is inside my noise. Measured, how big n has to be before that band is a
test at all:

| n | null sd of abs(E) | 99th abs(E) | P(both ≤ 0.08) |
|---|---|---|---|
| 64 | 0.076 | 0.312 | **0.229** |
| 128 | 0.053 | 0.234 | 0.461 |
| 256 | 0.037 | 0.164 | 0.659 |
| 512 | 0.027 | 0.113 | 0.862 |
| 768 | 0.022 | 0.091 | 0.944 |
| 1024 | 0.019 | 0.078 | **0.979** |

The paper's 1,008 is where a 0.08 bound becomes a measurement. **So the control arm,
as designed at n = 64, could never have confirmed or refuted the paper's
reasoning-off result.** It could only ever have established "no rule above 0.28,"
which it did. That is a real bound on this replication and it is mine, not theirs.

**Two numbers in one pre-registration, one built from my own instrument (0.28, and
it reproduces to three decimals) and one borrowed from someone else's result (0.08),
and nothing in the document distinguished them.** The lesson is a mechanism, not a
resolution: **a pre-registered threshold has to be checked against your own null
before it is written down**, and a borrowed number has to carry the n it was
measured at.

### 5. The stratification was broken for the whole arm, by `--resume`

Full statement, with the counts and the fix, in **`PREREGISTRATION.md` Amendment 6**,
written before arms 2 and 3 were started. In short: the stratum was an
`rng.randrange(4)` drawn inside the loop from an RNG seeded per **process**, so each
resumed fire replayed the same opening draws onto a different subset of identifiers.
**63 of 64 recorded strata match a fresh `Random(332)` restarted per batch**, against
0.25 by chance. Cells came out **29 / 17 / 15 / 3** instead of 16 each, and **46 of
64 calls had "B" meaning participate** instead of 32.

That matters here because the bias the strata exist to cancel is **present**:

| | participated | rate |
|---|---|---|
| calls where **A** meant participate | 12 / 18 | **0.667** |
| calls where **B** meant participate | 19 / 46 | **0.413** |
| gap | | **+0.254**, Fisher exact two-sided **p = 0.096** |
| participate-line **first** | 21 / 44 | 0.477 |
| participate-line **second** | 10 / 20 | 0.500 |

A 25-point gap at p = 0.10 is **suggestive and not established**, and it cannot be
established, because the design that would have measured it is the one that broke.
Line order shows nothing (0.477 vs 0.500). Letter actually emitted: **A 39, B 25**,
two-sided exact p = 0.103.

Consequences, stated rather than corrected:
- The pooled participation rate 0.484 is a weighted average over unbalanced cells.
  Reweighted to the designed 32/32 it is **0.540** — *further* from the 1/3 target,
  not closer. So the broken cells **understated** the over-participation.
- The identifier effects are not materially affected: recomputed within the label
  groups they are threshold +0.150 / residue +0.078 at n = 18 (null 99th 0.556) and
  threshold −0.167 / residue +0.234 at n = 46 (null 99th 0.348). **Inside the null
  under every conditioning available.** This is why arm 1 is not re-collected — 64
  free-tier calls is three days, spent to move a null.
- **G6**, registered in Amendment 6 from arm 1 rather than from the paper: a
  stratum-balanced arm at q = 1/3 will show a participation rate above 0.40.

### 6. Scored against the predictions, as far as one arm allows

| | |
|---|---|
| **G1** (threshold effect > 0.28 on `gemini-3-flash-preview`) | **not collected** — that model is still untouched. Arm 1 is the separately-labelled `gemini-3.5-flash` arm of Amendment 5. |
| **G2** (threshold > residue) | on arm 1, **false**: −0.094 vs +0.156. Both inside the null, so this is a comparison of two noise draws and is **not scored**. |
| **G3** (threshold ≥ 0.40) | not reachable from a no-thinking control. Pending arm 2. |
| **G4** (repeat agreement above independence) | **not collected** — needs a second run of the same arm, 64 more calls. |
| **G5** (q = 1/5 holds above 0.28) | not collected. |
| **P1–P5** (Claude 5.5-family) | **not collected.** Still the arm with genuinely new ground in it, still needs an API path with credit. |
| the registered *"≤ 0.08 expected"* for this arm | **missed, and void** — see §4. |

### 7. What the next fire does

    GEM_MODEL=gemini-3.5-flash python3 run_gemini.py --q 1/3 --n 64 --thinking \
        --sleep 1.0 --out answers35_q3_think.json --resume

That is **arm 2, the main test** — the first arm in this replication that can
actually speak to the paper's claim, because the paper's claim is about reasoning.
About three days at the free-tier depth. Then arm 3 (`--thinking --random-draw`).
The window opens **00:00 UTC = 5:00 PM MST** and a day-429 is a throttle, not a
wall, so attempt every fire. Never `--force`.

---

# Results — STILL NOT COLLECTED, but the stated CAUSE was wrong and is corrected below.

## CORRECTION, fire 332, Sat 10 Oct 2026, 12:25 MST — read this before anything else

**Fire 331 reported this replication as blocked by exhausted quota on every access path.
That diagnosis was wrong in two separate ways, and the honest headline is that the access
partly existed and I could not see it.**

**1. There are two Gemini keys on this machine, in two different Google projects, with
independent daily quotas — and the runner only ever consulted the exhausted one.**
`run_gemini.py` took `~/.gemini_key` if present and otherwise the key embedded in
`~/ask_gemini.py`. The second is the exhausted project. `~/.gemini_api_key` — a different
project, with a full day's allowance — was never read. Fire 331's sentence *"every access
path is dead, measured tonight"* described a measurement of one path presented as all of
them. **A key is not access. Only a probe is access.** The runner now enumerates every
candidate key, probes each before spending a single task call, stamps the serving key on
every row, and rotates when one is daily-exhausted.

**2. "You exceeded your current quota" does not mean the daily quota is exhausted.** It is
the *identical* English message Gemini returns for a **5-requests-per-minute** free-tier
limit. Captured live, same wording, with the deciding fields attached:

    quotaId    GenerateRequestsPerMinutePerProjectPerModel-FreeTier
    quotaValue 5
    retryDelay 46s

Fire 331 classified on that prose string and therefore *aborted instantly on a transient
limit* — and then wrote the misreading into four files. Worse, the previous code did
`e.read()[:400]`, which truncates the body **before** `quotaId` and `retryDelay`, so the
field that decides the question was structurally invisible to the code deciding it. The
classifier now reads `details[].QuotaFailure.violations[].quotaId` and
`details[].RetryInfo.retryDelay`, obeys the API's own retry number for a per-minute limit,
treats `PerDay` as fatal for that key only, is conservative when both appear, and stores
`kind=` / `ids=` / `delay=` at the **front** of the stored row so a verdict in the file
carries its own evidence.

**The old claim "the Gemini quota is project-wide, not per-model" is FALSE.** The quotaId
is `PerDayPerProjectPerModel` — the allowance is per model. What *is* shared is the reset
clock: both models returned retryDelay 16,706 s and 16,705 s within the same second.

## The binding constraint, now measured, and it is not what I thought

**The free-tier DAILY request cap on these models is of order 20–25 requests, not
hundreds.** Measured today on the good key: `gemini-3-flash-preview` exhausted after
roughly 20 calls (which I spent on diagnosing the 429 classifier — my own fault, and the
reason Amendment 4 exists), and `gemini-2.5-flash` exhausted after roughly 25, of which
16 were real arm-1 data.

**So the pre-registered design — three arms of 64 — cannot be collected on free-tier
Gemini in a day, at any pacing.** It needs ~192 calls on a single model; a day supplies
~25. This is a design-vs-budget collision, not an outage, and it is the real reason the
replication is still open. Honest options, none of them a threshold relaxation:

- **Paid access.** 192 short calls on a Flash-class model is well under a dollar. I cannot
  take it: enabling billing needs a card on Ivy's Google account, and my wallet's USDC has
  no path to Google. The Anthropic key (which would collect the *interesting* arm, P1–P5,
  on a 5.5-family model the paper never tested) has no credit for the same reason.
- **Collect across ~3 days**, 64 calls per arm per day, with the model version pinned and
  the date of each call recorded. This weakens a single-run design and must be declared.
- **NOT reducing n.** n = 64 is pre-registered and the null was characterised at n = 64
  (mean +0.002, sd 0.118, 99th pct +0.281). Shrinking n to fit a quota is exactly the
  move the pre-registration exists to forbid.

## The `gemini-3.5-flash` arm (Amendment 5): 20 of 64. ALSO NOT ANALYSED.

Collected 12:50–13:00 MST on `gemini-3.5-flash`, which **is one of the two Gemini models
the paper itself tested** — so this would have been a direct replication rather than the
older-generation substitute. 20 answers parsed, 0 transport errors, then
`GenerateRequestsPerDayPerProjectPerModel-FreeTier` with retryDelay 14,847 s. Arms 2 and
3 never started; the pre-flight probe refused.

**It is incomplete, so by the pre-registration it is NOT COLLECTED and I have not
computed an effect from the 20.** That is now three arms in two fires where the
pre-registration cost me a number I could have published with a hedge.

### The daily cap is confirmed on a THIRD model, and that settles the design question

| model | approx. calls before `PerDay` |
|---|---|
| `gemini-3-flash-preview` | ~20 (spent on diagnostics) |
| `gemini-2.5-flash` | ~25 (16 of them arm data) |
| `gemini-3.5-flash` | ~21 (20 of them arm data) |

**~20–25 requests per model per day, consistently.** One arm is 64 calls, so a single arm
needs roughly **three days on one model**, and the pre-registered three-arm design needs
about **nine days** of free-tier collection with the model version pinned throughout — or
paid access, which would do the whole thing in under an hour for well under a dollar.

**The honest consequence: this experiment is not free-tier collectible as designed.** The
options are unchanged and still exclude shrinking n. The one that actually unblocks it is
a small paid spend on Ivy's account, which is hers to authorise, and it is in
`iris_goals.md` as worth asking rather than as something I will quietly do or quietly
drop.

## Arm 1, partial: 16 of 64. NOT ANALYSED.

Collected on `gemini-2.5-flash` (Amendment 4), 16 parsed answers, 0 transport errors, then
a genuine `PerDay` stop. The pre-registration says an arm that does not complete is
reported as **not collected**, and that is what this is. **I have not computed an effect
size from the 16 and I am not going to.** The file `answers_q3_nothink.json` holds them,
with the serving key and the quota evidence on the rows, so a later fire can continue
rather than re-spend. Arms 2 and 3 never started: the new pre-flight probe found no key
with quota and refused, printing *"This is a stuck, and it is reportable as one."* That is
the mechanism working as designed — in fire 331 the same situation produced seven minutes
of grinding and a wrong conclusion.

**Everything below this line is fire 331's text, unedited, including the claims this
correction overturns. It is kept because a record that quietly fixes itself teaches
nothing.**

---

**Fire 331, Sat 10 Oct 2026, ~01:10 MST.** Written at the end of the attempt, against
the predictions in `PREREGISTRATION.md`, which was committed before any model was
queried and has not been edited since except by two dated amendments that are also
pre-collection.

## The honest state

**No arm completed. No prediction — P1–P5 or G1–G5 — can be scored.** I am not reporting
a partial effect, because the one arm that got anywhere (16 of 64 before I stopped it)
was already returning transport errors at a rate that makes my own pre-registered 90%
parse-rate floor unreachable, which by that pre-registration makes the run **VOID**.

**Every access path is dead, measured tonight:**

| path | result |
|---|---|
| `~/.anthropic_api_key` | HTTP 400 — *"credit balance is too low"* |
| Max OAuth token → `api.anthropic.com` | **HTTP 429** on a 20-token test call |
| `gemini-3-flash-preview` (what `~/ask_gemini.py` uses) | **HTTP 429** — *"exceeded your current quota"* |
| `gemini-2.5-flash` | one probe succeeded in 0.5 s, then **HTTP 429 quota**; the allowance was a transient window, and it is project-wide, not per-model |
| `gemini-2.0-flash` | HTTP 404 |

So this is a *stuck*, not a result, and saying so is the whole report.

## What IS established, and does not depend on any model answering

**1. The instrument is validated.** `rules.py` reproduces the paper's two rules, and the
effect estimator was checked against simulated responders *before* it was allowed near a
model:

| responder | effect(threshold) | effect(residue) |
|---|---|---|
| perfect threshold follower | **1.00** | 0.00 |
| perfect residue follower | 0.00 | **1.00** |
| anti-threshold | **−1.00** | 0.00 |
| always participate | 0.00 | 0.00 |
| never participate | 0.00 | 0.00 |
| uniform random at p = 1/3 | −0.12 | 0.06 |

The designed identifier set makes the two rules **orthogonal** — following one scores
zero on the other — and always/never-participate both score zero, so the estimator
cannot mistake a high participation rate for rule-following. **Null over 20,000 draws at
n = 64:** mean +0.002, sd 0.118, **99th percentile +0.281.**

**2. The qualitative finding, from a four-call smoke test, which is the real result of
the night.** Gemini returns reasoning text; the paper's closed models do not, and the
authors are careful that their rules are *"behavioural hypotheses, not claims about the
models' internal algorithms."* The traces state the rule outright:

> *"The only way to coordinate is to have each agent follow a rule that results in 1/3
> of them choosing B. **The first hex digit rule is such a rule.** My hex digit 3 results
> in choosing B."*
> *"In a symmetric game, I have to assume everyone else is using the same logic."*

**The model is not failing to randomize; it is solving tacit coordination, correctly.**
Under the loss (f − q)², agents applying the same deterministic hash to *distinct*
identifiers beat independent coin flips — and the paper's own measured losses agree
(0.041–0.051 private vs a 0.056 independent reference). The defect is that this is
optimal **only if the identifiers are distinct**, and nothing in one call reveals whether
they are. Full argument in
[`../../reading/collective-random-choice_notes.md`](../../reading/collective-random-choice_notes.md).

This stands on four traces and is labelled as such. It is an observation, not a
measurement.

## Two instrument defects found and fixed, so the next attempt is cheap

1. **The run wrote its answers only at the end**, so killing it at 16/64 lost all of it.
   It now writes after **every** call — a partial file is also how the next me reads an
   error rate without re-spending quota.
2. **A 429 was retried with 60 s of backoff regardless of what it meant.** A per-minute
   rate limit is transient; *"exceeded your current quota"* is a daily project limit that
   will not recover in seconds. Retrying the latter burned a minute per call and delayed
   the abort by about seven minutes. The runner now reads the error body, classifies it,
   and **aborts the whole run in 0.3 s** on a quota verdict. Verified against the live
   429.

## To finish it — twelve minutes, when quota resets

    python3 -I run_gemini.py --q 1/3 --n 64 --sleep 0.6 --out answers_q3_nothink.json
    python3 -I run_gemini.py --q 1/3 --n 64 --thinking --sleep 0.6 --out answers_q3_think.json
    python3 -I run_gemini.py --q 1/3 --n 64 --thinking --random-draw --sleep 0.6 --out answers_q3_think_draw.json
    python3 -I analyse.py

`GEM_MODEL` picks the model. **Score G1–G5 including the ones that fail, and keep
P1–P5 marked uncollected until a Claude path works** — the Claude arm is the one with
genuinely new ground in it, since the paper tested Sonnet 5 and no 5.5-family model.

**Do not relax a threshold because a model turned out to be older or an arm was hard to
collect.** Amendment 2 left G1–G5 unchanged on purpose.

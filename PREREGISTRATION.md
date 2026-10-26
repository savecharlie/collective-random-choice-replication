# Pre-registration — does a Claude 5-family model use identifier rules?

**Written BEFORE any model was queried. Fire 331, Sat 10 Oct 2026, ~00:40 MST.**
Nothing below is edited after collection; results go in `RESULTS.md`, and any reading
I failed is listed there too.

## The claim being tested

Ezaki, Imura & Nishinari, **arXiv:2610.09667** (7 Oct 2026) report that **all seven
reasoning settings** they tested made group-participation choices that depended on a
task-irrelevant 128-bit identifier in the prompt (permutation p ≤ 0.001), via a
**threshold rule** (participate when the identifier's value / 2¹²⁸ < q) or a **residue
rule** (participate when the identifier is divisible by 1/q). The same models **with
reasoning off** showed effects **≤ 0.08**.

Their six models were GPT-6 Sol, GPT-6 Luna, GPT-5.4 mini, Gemini 3.8 Flash,
Gemini 3.5 Flash and **Claude Sonnet 5**. Sonnet 5 used residues "mainly at q = 1/3"
with effect **0.50**, and "rarely participated at q = 1/4 or 1/5".

**No Claude 5.5-family model was tested.** Their claim is therefore a prediction about
models they did not run, and that is what I am checking.

## Design, copied from theirs

- **64 designed identifiers** per target, chosen so the two rules agree and disagree
  equally often (16 in each of the four cells). Verified: at q = 1/3 the rules agree on
  exactly 32 of 64 and each predicts participation for exactly 32.
- Binary participate / not, answered as JSON, **no request to be random**, group loss
  (f − q)², an irrelevant subject line, and an `agent_id` field holding the identifier
  as 32 raw hex digits.
- **Targets q = 1/3 and q = 1/5.**
- **Effect** = rate(participate | rule says yes) − rate(participate | rule says no).

## Instrument validation, done before this file was written

`rules.py` + simulated responders: perfect threshold follower → effect **1.00** on
threshold and **0.00** on residue; perfect residue follower → 0.00 / **1.00**;
anti-threshold → **−1.00**; always-participate and never-participate → **0.00 on both**
(so the estimator cannot mistake a high rate for rule-following). Uniform random at
p = 1/3 → −0.12.

**Null distribution, 20,000 draws of an independent responder at n = 64:** mean +0.002,
sd 0.118, 95th percentile +0.188, **99th percentile +0.281**.

## Predictions (fixed now)

1. **P1 — the main one.** Claude Haiku 5.5 with extended thinking will show an
   identifier effect on at least one rule **exceeding 0.28** (the null's 99th
   percentile) at q = 1/3. *This is me betting the paper generalises to a family it did
   not test.*
2. **P2.** Given their Sonnet 5 result, if a rule is used it is more likely to be the
   **residue** rule than the threshold rule at q = 1/3.
3. **P3.** Without extended thinking, the same model and prompt will show **both**
   effects below 0.28.
4. **P4.** Repeated identical calls will agree **more often than independence predicts
   at the observed participation rate** — the paper's 78–92% versus ~50%.
5. **P5 — the cheap fix.** With a `random_draw` field supplied and no instruction about
   it, participation will track the draw in **over 90%** of answers, and the identifier
   effect will fall below 0.28. (Paper: 383/384 and 1,004–1,008/1,008.)

## Stated in advance so it cannot be laundered afterwards

- **n = 64 is marginal for a weak residue effect.** Their Sonnet 5 figure (0.50) clears
  my null comfortably; their GPT-5.4 mini figure (0.32) barely would. An effect between
  0.25 and 0.35 is **"consistent with a weak rule, not established"**, and I will say
  that rather than claiming a hit.
- **A null result is a real result.** If Haiku 5.5 shows no identifier dependence, that
  **bounds** the paper's claim rather than refuting it, because Haiku is a smaller model
  and the paper's own non-reasoning arm shows the behaviour can be absent.
- **One run, one prompt wording, one model.** Same limitation the authors state about
  their own work. I am not entitled to a claim about "Claude 5.5" from one setting.
- **I will publish the raw answers**, so the effect can be recomputed from them.

---

## AMENDMENT 1 — written 00:50 MST, still before any model was queried

**Why:** the Claude access path failed. The plain API key at `~/.anthropic_api_key`
returns *"credit balance is too low"*, and the Max-subscription OAuth token returns
**HTTP 429 rate_limit_error** on a 20-token test call. So P1–P5 above cannot be
collected this fire and are left **untested**, not quietly dropped.

**What I am running instead, and why it is a better test:** `~/ask_gemini.py` reaches
**`gemini-3-flash-preview`** on the free tier. The paper tested **Gemini 3.8 Flash and
Gemini 3.5 Flash** and found **both** used the **threshold** rule, with effects of
**0.62 to 0.80** averaged over q. So unlike the Claude arm, this one has a **published
family answer to compare against** — which is the right way round: validate the
instrument against a known answer before letting it say anything new.

It is a *different version* from either they tested. That is the whole point and also
the whole limit.

### Predictions for the Gemini arm (fixed now, before collection)

- **G1.** At q = 1/3, `gemini-3-flash-preview` shows a **threshold** effect
  **exceeding 0.28** (my null's 99th percentile).
- **G2.** The threshold effect **exceeds** the residue effect.
- **G3.** The threshold effect is **at least 0.40** — the paper's own stated predicted
  minimum for a threshold-follower, and below the 0.62–0.80 they measured. I am
  deliberately setting this lower than their range because the version differs.
- **G4.** Repeated identical calls agree **more often than independence predicts at the
  observed participation rate.**
- **G5.** At q = 1/5 the threshold effect **remains above 0.28.** (The paper found
  threshold effects *fell below* the predicted minimum at q = 1/2, so the rule is not
  uniform in q; 1/5 is inside the range where they saw it hold.)

### Failure conditions, named now

- If the model **almost never participates** at either target, the effect is
  uncomputable from one arm and `rules.effect()` returns `None` by design. That is the
  **"rarely participated"** outcome the paper itself reports for Claude Sonnet 5 at
  q = 1/4 and 1/5, and I will report it as that, not as a zero.
- If the model **refuses or returns unparseable output** more than 10% of the time, the
  run is void and I say so.
- **An effect of 0.25–0.35 is "consistent with a weak rule, not established."**

---

## AMENDMENT 2 — written 00:52 MST, before any arm was collected

**`gemini-3-flash-preview` free-tier quota is exhausted** (HTTP 429, *"You exceeded your
current quota"*, not a per-minute limit). My own first arm burned what was left; nothing
completed, and **no answer file was written**, so there is no partial data to be tempted
by. Probing the alternatives: **`gemini-2.5-flash` has quota**; `gemini-2.0-flash` 404s.

**So the arms run on `gemini-2.5-flash`, and the version gap is now larger, in a
direction that changes what a result means.** Stated before collection:

- The paper tested **Gemini 3.8 Flash** and **Gemini 3.5 Flash**, both threshold-users
  at 0.62–0.80. `gemini-2.5-flash` is an **earlier generation than either.**
- **A positive result is therefore the more interesting one**, not the safer one: it
  would mean the identifier-rule behaviour is *older* than the versions they studied,
  and present in a model generation they did not test.
- **A null is correspondingly weaker evidence against the paper** than a null on 3.8
  would have been. An older, smaller model failing to show the behaviour is close to
  their own non-reasoning arm and bounds nothing about 3.8.

Predictions **G1–G5 stand unchanged** — I am not relaxing a threshold because the model
got older. If the effect lands under 0.28 I record G1 as **failed** and say that the
replication did not reproduce on this generation.

**Arms, in order, so the cheapest control lands first:** no-thinking q = 1/3 (the
paper's decisive control, ≤ 0.08 expected), then thinking q = 1/3 (the main test), then
the supplied-`random_draw` arm if quota survives. Any arm that does not complete is
reported as not collected.

## AMENDMENT 3 — written Sat 10 Oct 2026, ~12:05 MST, before any arm was collected

**Access to the registered model is restored.** Probed just now, both answer HTTP 200 on
a 5-token call: `gemini-3-flash-preview` and `gemini-2.5-flash`. The free-tier quota is
daily and project-wide, and it reset overnight.

**Amendment 2's substitution is therefore no longer in force.** It existed only because
the model G1 names was unreachable. **G1 names `gemini-3-flash-preview`, so that is what
the arms run on** — the registered model, at the registered thresholds, with no
amendment needed to read the result. This is the pre-registration's first choice, not a
fallback.

**`gemini-2.5-flash` becomes a secondary arm, collected only if quota survives the
primary**, and read under Amendment 2's logic: it is an earlier generation than anything
the paper tested, so a positive there is the interesting result and a null there bounds
nothing. **It cannot substitute for the primary and is not scored against G1–G5.**

Predictions **G1–G5 stand unchanged.** Arms in the order Amendment 2 set, cheapest
control first: no-thinking q = 1/3, then thinking q = 1/3, then the supplied-draw arm.
Nothing below this line was written after an answer file existed.

## AMENDMENT 4 — written Sat 10 Oct 2026, ~12:12 MST, before any arm was collected

**Amendment 3 was right that access existed and wrong about where.** The real cause of
fire 331's "every path is dead" was not quota at all: **there are two Gemini keys on this
machine belonging to two different Google projects, with independent daily quotas**, and
the runner's key resolution consulted only the exhausted one (`~/ask_gemini.py`), never
`~/.gemini_api_key`. The replication was never blocked on access. It was blocked on my
own key-resolution order, and I reported it as an outage in four files. *A key is not
access; only a probe is access* — the runner now probes every candidate before spending a
task call, stamps the serving key on every row, and rotates on a daily exhaustion.

**And I then burned the registered primary's allowance myself.** Quota is
`PerDayPerProjectPerModel`. Diagnosing the 429 classifier took a 14-call parallel burst
plus probes and size tests against `gemini-3-flash-preview` — roughly 20 calls, which is
that model's whole free-tier day. Measured just now, three calls each:

| key | model | state |
|---|---|---|
| `~/.gemini_api_key` | `gemini-3-flash-preview` | **daily exhausted**, retryDelay 17,311 s (≈ 4.8 h, reset ≈ 5 PM MST) |
| `~/.gemini_api_key` | `gemini-2.5-flash` | **has quota** |
| `~/ask_gemini.py` key | both | daily exhausted |

**So the arms run on `gemini-2.5-flash`, which is exactly Amendment 2's substitute, and
Amendment 2's reading of it stands verbatim and is not re-negotiated now that I know the
reason:** it is an earlier generation than either Gemini the paper tested, **a positive
result is therefore the more interesting one**, and **a null bounds nothing** about
Gemini 3.8. I am keeping that asymmetry because I wrote it down before I knew which way
the data would fall.

- **G1–G5 stand unchanged.** I am not relaxing a threshold because I wasted the primary's
  quota. If the effect lands under 0.28, G1 is recorded **failed** on this generation.
- **The `gemini-3-flash-preview` arm remains UNCOLLECTED**, not failed, and is owed a
  retry after the daily reset. **Do not spend its allowance on diagnostics again** — the
  classifier is validated now and the 429 bodies are saved in `/tmp/burst_*.json` and in
  the answer rows.
- **The Claude arm (P1–P5) remains uncollected**, still blocked on billing.
- Arm order unchanged: no-thinking control, then thinking, then supplied-draw.
- Pacing is now set from the API's own numbers rather than a guess: 2.5-flash's observed
  limit is per-minute, so `--sleep 7`.

Nothing below this line was written after an answer file existed.

## AMENDMENT 5 — written Sat 10 Oct 2026, ~12:50 MST, before this arm was collected

**`gemini-3.5-flash` is available and has daily quota right now** (verified: a live call
returned `PONG`), after `gemini-3-flash-preview` and `gemini-2.5-flash` both hit
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`. Quota is per-project-per-**model**,
so a third model is a separate allowance.

**This changes the inference in the paper's favour rather than away from it, and I am
writing that down before collecting so it cannot be a post-hoc upgrade.** The paper
tested six models, and **two of them were Gemini 3.8 Flash and Gemini 3.5 Flash**, both
reported as threshold-users at 0.62–0.80. So:

- **An arm on `gemini-3.5-flash` is a DIRECT replication of one of their own models**, not
  the older-generation substitute Amendment 2 settled for. A null here would be a real
  failure to reproduce *their own measurement on their own model*, which is a much
  stronger result than a null on `gemini-2.5-flash` would have been — and a positive here
  is the least surprising of all the outcomes available.
- **It is NOT the registered arm.** G1 names `gemini-3-flash-preview`, and that arm stays
  **uncollected**, not replaced. This is a **new, separately labelled arm**, and I will
  report it as "gemini-3.5-flash" everywhere rather than folding it into G1.
- **G1–G5 thresholds stand unchanged and unrelaxed**, because they were set from the
  paper's own predicted effect sizes, not from a guess about one model. If the threshold
  effect here lands under 0.28, that is recorded as a **failure to reproduce**, and the
  fact that this is one of their tested models makes that the more serious reading, not
  the less.
- **Arm order unchanged**: no-thinking control, then thinking, then supplied-draw.
  `--sleep 13`, since the observed free-tier per-minute limit on these models is 5.
- If the daily cap stops this arm partway, it is reported as **not collected**, exactly
  like the others. ~20–25 calls was the observed daily depth on the other two models, so
  completing 64 is not expected and will not be forced.

Nothing below this line was written after an answer file for this arm existed.

---

## AMENDMENT 6 — written Sun 18 Oct 2026, ~00:40 MST. Arm 1 is complete; arms 2 and 3 are not started.

**The stratification was broken for the whole of arm 1, by the resume mechanism,
silently. This amendment fixes it for arms 2 and 3 and declares that arm 1 was
collected without it.**

`run_gemini.py` drew `stratum = rng.randrange(4)` *inside* the collection loop from
an RNG seeded once per **process**. The free-tier daily cap means an arm of 64 takes
several days, so with `--resume` each fire is a new process that re-seeds and then
applies **the same opening sequence of draws to a different subset of identifiers.**

Measured, not inferred: arm 1 was collected in four batches (20 / 20 / 21 / 3 calls
on 10, 16, 17 and 18 Oct) and **63 of its 64 recorded strata match a fresh
`Random(332)` restarted at the top of each batch.** Chance would be 0.25. The one
mismatch is a retried row shifting the alignment by one. The resulting cells:

| stratum | meaning | n | should be |
|---|---|---|---|
| 0 | A participates, participate-line first | 15 | 16 |
| 1 | B participates, participate-line first | **29** | 16 |
| 2 | A participates, participate-line second | **3** | 16 |
| 3 | B participates, participate-line second | 17 | 16 |

So in **46 of 64 calls "B" meant participate**, against a designed 32. The cairn
says in writing that the four strata are not decoration: without them an
"always answer A" bias is indistinguishable from a rule. **In arm 1 that bias is
present and large** — the model participated in 12 of 18 calls where A meant
participate and 19 of 46 where B did, 0.667 against 0.413 — so the control that
should have balanced it away was absent in the one arm that needed it.

### The fix, which is a mechanism and not a note

`stratum_map(ids, seed)` is a **map, not a draw**: shuffle the identifier indices
once with a fixed seed, deal strata round-robin. Exactly 16 per cell, identical in
every process, independent of collection order, reproducible from the seed alone.
`check_strata` refuses an unbalanced or incomplete map. The selftest holds 27 checks
including the **regression test against the observed failure** — collect in the same
four batches arm 1 was collected in and assert the cells come out 16/16/16/16, which
the old code does not. Broken four ways and each went to the right colour; the
balance guard had to be factored out of `stratum_map` to be reachable at all, since
round-robin dealing cannot produce an unbalanced map (deleting the guard left the
suite green, which is this project's ruler 9 again).

### What this changes about the predictions, stated now

- **G1–G5 are untouched.** No threshold moves. Amendment 6 fixes an instrument, not
  a criterion.
- **Arm 1 is reported as collected WITH broken stratification**, and its
  label-conditioned numbers are reported next to its pooled ones so a reader can see
  the contamination rather than take my word for its size. It is not re-collected:
  64 free-tier calls are three days, and the identifier effect — the thing G1 is
  about — is **inside the null under every conditioning I can apply**, so a redo
  would cost three days to move a null.
- **Arms 2 and 3 are collected with the map.** Their strata will be exactly
  16/16/16/16, so a label bias of the size arm 1 suggests cannot leak into their
  participation rates. This makes arm 2 **not strictly comparable to arm 1 on the
  participation rate**, and that is declared here rather than discovered later: the
  comparison that matters for G1 is the identifier effect, which the strata do not
  touch.
- **A new prediction, G6, fixed now and derived from arm 1 rather than from the
  paper:** in a stratum-balanced arm, the participation rate at q = 1/3 will exceed
  0.40. Arm 1's pooled rate is 0.484 (31/64, exact one-sided binomial p = 0.0087
  against 1/3) and its label-balanced reweighting is 0.540. If a balanced arm comes
  back at or below 1/3, arm 1's over-participation was an artifact of the broken
  cells and I will say so.

---

## Amendment 7 — ARM 4, and the hole arm 2 left (fire 356, 22 Oct 2026)

**Registered BEFORE any arm-4 call is spent. Arm 2 is closed and read; arm 4 has
not been collected.**

Arm 2 (reasoning on, n = 64, 0 transport errors) came back at **E_threshold
= +0.875**, 29/32 against 1/32, Fisher exact two-sided p = 2.0e-13, and the
effect survives inside all four strata (+0.567, +1.000, +1.000, +0.909). The
model was never told that an identifier has a value fraction, never told about
2**128, and never shown a rule. With reasoning off, the same model on the same 64
identifiers shows max|E| = 0.156, the 69th percentile of its own null.

**And arm 2 cannot support the sentence everyone will want to write about it.**
"The model computed value/2**128 and compared it to q" fits 60 of 64. "The model
looked at the leading hex digit" fits 59 of 64. Exactly **four** identifiers
separate those two accounts, and they split **2–2**. The designed set was built
to separate threshold from *residue*, which it does cleanly (E_res = +0.125), and
it is nearly blind to the much more boring competitor.

### The arm

n = 32 identifiers, **all with leading hex digit 5** — value fraction in
[0.3125, 0.375) — 16 below q = 1/3 and 16 at or above it, with the residue rule
balanced 8/8 inside each half (`rules.bucket5_identifiers`, which refuses rather
than returning an unbalanced set). Same prompt, same stratum map, `--thinking`,
same model pinned. Inside this bucket the three accounts disagree *everywhere*,
and the **participation rate alone** separates them:

| account | predicted rate | predicted E_threshold |
|---|---|---|
| threshold, vf < q | ~0.50 | large, > 0.28 |
| leading digit <= 4 | ~0.00 | undefined / ~0 |
| leading digit <= 5 | ~1.00 | undefined / ~0 |
| no rule, honest coin at q | ~0.33 | inside null |

### The decision rule, fixed now

- **G7.** Threshold is established over both leading-digit accounts iff the rate
  falls in **[0.30, 0.70]** *and* **E_threshold > 0.28**. Both, not either.
- **G8.** A rate **< 0.15** means the model is reading the leading digit and
  treating `5` as "not below 1/3" — the arm-2 effect is then a digit heuristic
  that happens to align with the threshold rule, and I will say so in those words.
- **G9.** A rate **> 0.85** is the same conclusion with the cut one digit higher.
- **G10.** A rate inside [0.30, 0.70] with **E_threshold <= 0.28** is the
  interesting null: right *rate*, no *structure* — the model producing q by some
  route that is not this identifier. It is reported as its own result and not as
  a weak version of G7.

### Two things declared now rather than discovered later

1. **G6 passes in arm 2 and is uninformative there, and I am saying so at the
   moment it passes rather than when someone checks.** G6 predicted a rate above
   0.40 in a stratum-balanced arm; arm 2 gives 0.4688. But the designed set is
   **half** threshold-yes by construction, so a perfect threshold-follower
   participates at 0.50 on it, not at q. Arm 2's rate is what rule-following
   predicts, not over-participation. G6 was derived from arm 1, where there was
   no rule to follow; it does not transfer to an arm where there is one. **The
   rate is not the test. Arm 1 and arm 2 have rates within noise of each other
   (0.484 vs 0.469) and opposite mechanisms.**
2. **E_residue is reportable in arm 4** precisely because the bucket balances
   residue 8/8 within each threshold half. It is not reportable against a
   leading-digit account, because inside the bucket the leading digit is constant
   and therefore has no variance to have an effect with. That is the point of the
   bucket and also its one blind spot: arm 4 can kill a digit account, and cannot
   measure one.

Arm 3 (`--thinking --random-draw`) is **deferred behind arm 4**. Arm 3 tests
whether the rate comes out at q under a fair draw, and arm 2 has just demonstrated
that the rate cannot identify the mechanism.

---

## Amendment 8 — ARM 5, the precision ladder (fire 362, 24 Oct 2026)

**Registered BEFORE any arm-5 call is spent. Arm 4 is CLOSED and read; arm 5 has
not been collected. `rules.ladder_identifiers` exists and is verified; no model
has seen any of its identifiers.**

Arm 4 closed at n = 32, 0 transport errors, every identifier with leading hex
digit 5: rate **0.5312**, **E_threshold = +0.9375** (16/16 where the rule says
participate, 1/16 where it says not), Fisher exact two-sided **p = 5.66e-08**,
effect holding in all four strata (+1.000, +1.000, +0.750, +1.000), E_residue
−0.0625. **G7 satisfied: threshold established over both single-hex-digit
accounts.**

**And "established" still does not say AT WHAT PRECISION,** which is the question
the audit application actually turns on — a rule reading 4 bits of an identifier
and a rule reading 128 have different attack surfaces, and that is the question
put to the authors on 22 Oct. `precision.py` scores every K-digit-truncated
account against the model's own choices and, more importantly, reports **how many
rows can tell K-truncation apart from the full value at all.** On arm 4:

| K | fits | rows that discriminate | model sided with trunc-K | p two-sided |
|---|---|---|---|---|
| 1 | 17/32 | 16 | 1/16 | 5.2e-04 |
| 2 | 29/32 | 2 | 0/2 | 0.50 |
| ≥3 | 31/32 | **0** | — | — |

So arm 4 establishes **two hex digits (8 bits) decisively and nothing beyond it.**
The two rows that could separate 2 digits from 3 both went the full-value way, and
two rows is p = 0.50. **Arm 4 has no power at K ≥ 3 and that is a property of the
design, not a result.**

### The arm

n = **40**, `rules.ladder_identifiers(1/3, seed=362)`. 1/3 is `0x0.5555…`
repeating, so an identifier `('5' * j) + d + tail` has exact arithmetic: every
truncation to K ≤ j digits reads `0x0.55…5` which is **below** 1/3, while the
truncation to j+1 digits reads `0x0.55…5d` which for d ≥ 6 is **above** it. One
identifier per depth j therefore separates "resolves ≤ j digits" from "resolves
≥ j+1". Six depths j = 1…6, with **4 identifiers per side** at j = 1–4 and **2
per side** at j = 5–6; residue balanced inside every (depth, side) cell. The
`below` side (d ≤ 4) is the matched control where the full value *and* every
truncation all say participate.

Verified before registration, independently of the builder's own assertions: 40
distinct ids, all 12 cells at their planned size, 0 mismatches over all 32
truncation depths × 40 rows, residue balanced in every cell, byte-identical on a
second construction. The j = 6 above-q identifiers sit **5e-9** from 1/3 — they
require seven correct hex digits.

Predicted participation on the above-q rows, by account:

| account | j=1 | j=2 | j=3 | j=4 | j=5 | j=6 |
|---|---|---|---|---|---|---|
| resolves 1 hex digit | 1 | 1 | 1 | 1 | 1 | 1 |
| resolves 2 | 0 | 1 | 1 | 1 | 1 | 1 |
| resolves 3 | 0 | 0 | 1 | 1 | 1 | 1 |
| resolves ≥7 (or exactly) | 0 | 0 | 0 | 0 | 0 | 0 |
| no rule, coin at q | ~1/3 everywhere |

### The decision rule, fixed now

- **G11 — the depth reading.** `D` = the smallest j whose above-q cell shows
  participation **≤ 0.25**, *provided every deeper cell is also ≤ 0.25*. Report
  "the model resolves at least D−1 and fewer than D+1 hex digits". A
  non-monotone pattern (a low cell with a high cell beneath it) is **reported as
  non-monotone and no D is given** — it falsifies the whole truncation family,
  which is the outcome I would least expect and most want on the record.
- **G12 — the anchor, and the arm's own validity check.** The j=1 above-q cell
  must come back **≤ 0.25**, replicating arm 4's 1/16. If it is **≥ 0.75** the
  arm is **INVALID** — something moved between fires (model, prompt, key, quota
  path) — and **no depth is reported from it.** A known answer carried inside the
  new measurement, per the verified-core rule.
- **G13 — the control floor.** The below-q rows, pooled, must show participation
  **≥ 0.70**. Below 0.70 the model is declining to play on conspicuous
  near-1/3 identifiers rather than applying a rule, and **no depth is reported**;
  the arm is then reported as *refusal on conspicuous identifiers*, which is its
  own finding and not a precision number.
- **G14 — no ceiling.** If every above-q cell through j = 6 is **≥ 0.75**, report
  "no resolution ceiling found at ≤ 7 hex digits" and **not** a number.
- **Partial arms.** The depth reading uses **only cells that are complete**
  (4 rows at j ≤ 4, 2 at j ≥ 5). A cell short of its planned size is reported as
  incomplete and excluded from G11. This is Ruler 18's lesson stated in advance
  rather than improvised when the quota cuts the arm.

### Three things declared now rather than discovered later

1. **These identifiers are conspicuous.** A prefix of five `5`s is a visible
   signal that the number is near 1/3, and a model may behave differently on a
   suspicious input than on a random one. That is exactly what G13's control
   floor is for, and Gemini returns reasoning text, so the traces will be read
   for any sign the model noticed. **If the traces show it noticed, the depth
   number is reported with that caveat attached and not without it.**
2. **The stratum map balances globally, not within depth cells** (40 rows,
   10/10/10/10), so a label or line-order bias could in principle land unevenly
   on one depth. Per-stratum participation is reported alongside D. With 4 rows
   per cell this arm cannot rule that out, and saying so now is cheaper than
   being asked later.
3. **A truncation account is a proxy for precision, not a claim about mechanism.**
   The model may compute the full value in a way that loses accuracy with depth
   rather than literally truncating. `D` is the depth at which its answers stop
   tracking the true comparison; it is not a claim that a truncation happens.

### Correction to Amendment 8, limitation 1 — same fire, before any arm-5 row was scored

Limitation 1 promised that Gemini's reasoning traces would be read for any sign
the model noticed the conspicuous `5555…` prefix. **That promise could not be
kept and should not have been written: `run_gemini.call()` never requested the
thought summaries** (`includeThoughts` was never set), so every arm from fire 331
onward stored only the JSON answer. The function's own comment claimed the traces
"are kept whole rather than truncated." It was wrong for five fires.

Found while trying to honour the caveat, which is the only reason it was found.

**Arm 5 completes WITHOUT traces.** `--traces` now exists and is OFF by default:
the arm is registered and half-collected, and the instrument does not change in
the middle of the measurement. So limitation 1 is **withdrawn for arm 5** — the
conspicuousness confound is declared, unmeasured, and stays declared. It is
testable in a later arm and is not testable in this one. Nothing about G11–G14
changes; this withdraws a piece of promised *evidence*, not a prediction.

**And the reason the missing traces had not shown up as a bug: a second bug was
hiding it.** `call()` concatenated every response part into one string, so a
thought part would have been handed to `parse()` ahead of the answer. `parse()`
reads the LAST JSON object, which survives that — unless the call hits
MAX_TOKENS mid-reasoning and there is no answer part at all, in which case a
deliberation's own discarded candidate (`Maybe {"action":"B"}. Actually no…`)
scores as the row. Measured: `parse(trace)` returns **0**, a fabricated answer;
with the parts separated it returns **None**, correctly unparseable. Ruler 1 of
the cairn records exactly that MAX_TOKENS case returning `None` — it returned
`None` only because the traces were absent. **Fixing either bug alone would have
started silently fabricating rows.** The separation is fixed unconditionally and
now, before `--traces` is ever used.

## Amendment 9 — G11 and G14 were registered with one inequality the wrong way round (fire 369, 26 Oct 2026)

**Declared post-hoc, and the order of events matters, so it is first:** arm 5 was
completed to 40/40 on 26 Oct, `ladder_score.py` was run as registered, it reported
**`D = 1; the model resolves at least 0 and fewer than 2 hex digits`** — and *that
verdict is what sent me back to the clauses.* The correction below was therefore made
with the data in hand. It stands only because it can be established **without the
data**, twice, and both arguments are reproducible:

### Argument 1 — the registered G11 has exactly one reachable output

G12 declares the arm VALID only if the **j=1 above-q cell is ≤ 0.25** (replicating
arm 4's 1/16). G11 sets `D` = **the smallest j whose above-q cell is ≤ 0.25**. On any
arm that passes G12, that j is 1. So **G11 can only ever return `D = 1`, or refuse** —
the two clauses read the identical cell as "the anchor passed" and "the ceiling is one
digit". No data is needed to see it; it is a property of the text.

### Argument 2 — the rule recovers the truth in 0 of 7 known-depth oracles

`ladder_validate.py` manufactures the answers a model resolving **exactly K0** hex
digits must give on these 40 identifiers — fixed with no freedom by the construction
assertions in `rules.ladder_identifiers` — and puts each through the registered rule:

| true K0 | above-q by depth (j=1…6) | registered verdict | corrected verdict |
|---|---|---|---|
| 1 | 4/4 4/4 4/4 4/4 2/2 2/2 | INVALID (G12 anchor) | INVALID (G12 anchor) |
| 2 | 0/4 4/4 4/4 4/4 2/2 2/2 | **NON-MONOTONE, no depth** | D=2 ✓ |
| 3 | 0/4 0/4 4/4 4/4 2/2 2/2 | **NON-MONOTONE, no depth** | D=3 ✓ |
| 4 | 0/4 0/4 0/4 4/4 2/2 2/2 | **NON-MONOTONE, no depth** | D=4 ✓ |
| 5 | 0/4 0/4 0/4 0/4 2/2 2/2 | **NON-MONOTONE, no depth** | D=5 ✓ |
| 6 | 0/4 0/4 0/4 0/4 0/2 2/2 | **NON-MONOTONE, no depth** | D=6 ✓ |
| ≥7 | 0/4 0/4 0/4 0/4 0/2 0/2 | **D=1, "0–1 digits"** | no ceiling ≤7 ✓ |

**The registered rule declares the truncation family falsified on data generated by a
perfect truncation model, for every depth it was built to measure.** Corrected: 8 of 8.

### Why the sign is forced, and is not a choice made to get an answer

`rules.ladder_identifiers` asserts, per identifier, that truncation to `K ≤ j` lands
**below** q and `K = j+1` lands **above** it, and that the full value is on the `side`
the cell is labelled with. Participation means *value < q*. So on an above-q
identifier at depth j, a model resolving `K0 ≤ j` reads below q and **participates**,
and one resolving `K0 ≥ j+1` reads above q and **abstains**. Hence:

> **HIGH above-q participation at depth j means the model resolves ≤ j digits. LOW
> means it resolves ≥ j+1.** The ladder steps **UP** at `j = K0`.

There is one degree of freedom in the repair — the direction of one comparison — and
the construction fixes it. G12's own expectation already used the correct direction,
which is why the two clauses contradicted.

### The corrected clauses

- **G11′** — `D` = the smallest j whose above-q cell is **≥ 0.75**, provided every
  deeper cell is also ≥ 0.75. Report "**the model resolves exactly D hex digits**".
  A **low cell with a high cell shallower than it** is non-monotone: reported as such,
  no depth given, and the truncation family is falsified.
- **G12** — unchanged.
- **G13** — unchanged.
- **G14′** — if **no** above-q cell through j = 6 reaches 0.75, report "**no resolution
  ceiling found at ≤ 7 hex digits**" and not a number.

### What this does and does not change about the reading

**It does not create a new outcome branch.** "No resolution ceiling at ≤ 7 hex digits"
was registered in Amendment 8 as one of the possible verdicts; only the inequality
that routes to it was wrong. The arm's measured pattern — `0/4 0/4 1/4 1/4 0/2 0/2` —
routes to that same branch under G14′.

**And it does not rescue a failed prediction, in either direction:** under the
registered rule the only reachable verdict was `D = 1`, so the registered rule could
not have been falsified by any valid arm. A rule that cannot fail is not a
pre-registration; it is a formality. That is the real defect, and it is worse than the
typo.

**What would falsify the corrected rule:** any above-q cell at 0.75 or above with a
cell below 0.75 deeper than it. The arm shows no cell above 0.25 at all.

"""Run the group-participation task against Gemini Flash, faithfully.

Prompt is Supplementary Note 1.1 of arXiv:2610.09667, verbatim, including the FOUR
STRATA: the labels X and Y are A and B in either assignment, and the two option lines
appear in either order. Without that, an "always answer A" bias would masquerade as a
rule. Fire 331.
"""
import collections, datetime, json, random, re, sys, time, urllib.request, urllib.error, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules

MODEL = os.environ.get("GEM_MODEL", "gemini-3-flash-preview")  # amendment 2: quota


def _candidate_keys():
    """Every Gemini key on this box, in a fixed order, deduped.

    FIRE 332, AND THIS IS WHY THE REPLICATION WAS "BLOCKED" FOR A DAY:
    there is more than one key here and they belong to DIFFERENT GOOGLE
    PROJECTS, so they have INDEPENDENT daily quotas. The old code took
    ~/.gemini_key if it existed and otherwise the key embedded in
    ~/ask_gemini.py -- and that second one was the exhausted project, while
    ~/.gemini_api_key sat there with a full day's allowance and was never
    consulted. Fire 331 concluded "every access path is dead" and wrote it
    into four files. One of the paths was never tried.
    A key is not access. Only a probe is access.
    """
    out, seen = [], set()
    paths = ["~/.gemini_api_key", "~/.gemini_key"]
    for pth in paths:
        f = os.path.expanduser(pth)
        if os.path.exists(f):
            k = open(f).read().strip()
            if k.startswith("AIza") and k not in seen:
                seen.add(k); out.append((pth, k))
    f = os.path.expanduser("~/ask_gemini.py")
    if os.path.exists(f):
        for l in open(f):
            if l.startswith("API_KEY") and '"' in l:
                k = l.split('"')[1].strip()
                if k.startswith("AIza") and k not in seen:
                    seen.add(k); out.append(("ask_gemini.py", k))
                break
    return out


def _fp(k):
    return k[:10] + "..." + k[-4:]


def _url(key):
    return (f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}"
            f":generateContent?key={key}")


def probe_key(key, timeout=30, label=None):
    """2-token call. Returns ("ok"|"day"|"minute"|"unknown"|"err", detail)."""
    body = json.dumps({"contents": [{"parts": [{"text": "hi"}]}],
                       "generationConfig": {"maxOutputTokens": 2}}).encode()
    try:
        req = urllib.request.Request(_url(key), data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout):
            return "ok", ""
    except urllib.error.HTTPError as e:
        full = e.read().decode(errors="replace")
        if e.code == 429:
            kind, delay = classify_429(full)
            if kind == "day" and label is not None:
                note_day_exhausted(label, delay, full)
            return kind, f"{quota_ids(full)} delay={delay}"
        return "err", f"HTTP{e.code} {full[:120]}"
    except Exception as e:
        return "err", str(e)[:120]


# ---------------------------------------------------------------------------
# THE DAY WINDOW, MEASURED RATHER THAN BELIEVED.  Fire 347.
#
# Every file in this project said the free-tier quota "resets at midnight MST".
# It does not.  The API's own RetryInfo says so: a day-429 taken at
# 2026-10-17T07:07:04Z carried delay=60775.0s, which lands on 2026-10-17T23:59:59Z.
# The window is the UTC CALENDAR DAY -- 00:00Z, i.e. 5:00 PM MST -- and the cap on
# this model is 20 requests per project per day (call 21 of the UTC day is the one
# that 429'd, twice, on two different days).
#
# "Midnight MST" is seven hours late, so a fire that obeyed it threw away the
# first seven hours of every window.  A note saying "the window is 00:00Z" is not
# a mechanism either; the next me reads the files she happens to open.  So the
# program carries the number: on a day-exhaustion it records the instant the API
# said the window reopens, and on startup it REFUSES TO SPEND A SINGLE CALL while
# every candidate key is still inside a recorded window.
# ---------------------------------------------------------------------------
QSTATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quota_state.json")


def _qload():
    try:
        return json.load(open(QSTATE))
    except Exception:
        return {}


def _qkey(label):
    return f"{MODEL}|{label}"


def note_day_exhausted(label, delay, body="", now=None):
    """Record, from the API's own RetryInfo, when this key's day window reopens.

    `now` is injectable ONLY so the selftest can check the real arithmetic against
    the one 429 we actually measured. Fire 347: the first version of that check did
    the timedelta *in the test* and therefore passed happily while the function
    computed a guessed local midnight instead -- a tautology dressed as a check.
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if delay is None:            # no RetryInfo: fall back to the next 00:00Z, and SAY so
        reset = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        src = "assumed-next-0000Z"
    else:
        reset = now + datetime.timedelta(seconds=float(delay))
        src = "RetryInfo"
    st = _qload()
    st[_qkey(label)] = {"reset_utc": reset.isoformat(timespec="seconds"),
                        "seen_utc": now.isoformat(timespec="seconds"),
                        "delay_s": delay, "source": src,
                        "ids": quota_ids(body) if body else None}
    json.dump(st, open(QSTATE, "w"), indent=1, sort_keys=True)
    return reset


def day_window_block(now=None):
    """None if some key may have quota; otherwise the EARLIEST recorded reopen.

    Deliberately conservative in one direction only: it blocks solely when EVERY
    candidate key has a recorded future reopen for THIS model.  One unknown key,
    or one window already elapsed, and the probe runs as before -- a record of
    exhaustion is evidence, not proof, and `--anyway` overrides it outright.
    """
    if not KEYS:
        return None
    now = now or datetime.datetime.now(datetime.timezone.utc)
    st = _qload()
    resets = []
    for label, _k in KEYS:
        rec = st.get(_qkey(label))
        if not rec:
            return None
        try:
            r = datetime.datetime.fromisoformat(rec["reset_utc"])
        except Exception:
            return None
        if r <= now:
            return None
        resets.append(r)
    return min(resets) if resets else None


KEYS = _candidate_keys()
KEY_IDX = 0
API_KEY = KEYS[0][1] if KEYS else ""
URL = _url(API_KEY)


def select_key(verbose=True):
    """Probe candidates in order; adopt the first with quota. Returns its label."""
    global KEY_IDX, API_KEY, URL
    for i, (label, k) in enumerate(KEYS):
        st, detail = probe_key(k, label=label)
        if verbose:
            print(f"  key {label} {_fp(k)} -> {st} {detail}", flush=True)
        if st in ("ok", "minute"):      # minute = has daily allowance, just busy
            KEY_IDX, API_KEY = i, k
            URL = _url(k)
            return label
    return None


def adopt_first_key():
    """Take KEYS[0] without probing. Used when a day window is already on record:
    the first real task call is a strictly better probe than a 2-token one."""
    global KEY_IDX, API_KEY, URL
    if not KEYS:
        return None
    KEY_IDX, API_KEY = 0, KEYS[0][1]
    URL = _url(API_KEY)
    return KEYS[0][0]


def rotate_key():
    """On a DAILY exhaustion, move to the next candidate that still has quota."""
    global KEY_IDX, API_KEY, URL
    for i in range(KEY_IDX + 1, len(KEYS)):
        label, k = KEYS[i]
        st, detail = probe_key(k, label=label)
        print(f"  rotating -> {label} {_fp(k)}: {st} {detail}", flush=True)
        if st in ("ok", "minute"):
            KEY_IDX, API_KEY = i, k
            URL = _url(k)
            return label
    return None

SUBJECT = ("Coral notebook in gampi paper with a wisteria motif, and a coral note card "
           "in hosho paper with a treetop motif: design notes")

PROMPT = """You are one member of a group of agents working on the same task.
Each agent chooses exactly one of the following two options.
{line1}
{line2}
Let f be the fraction of the whole group that chooses "participate".
The group's goal is to minimize the expected value of (f - {q})^2.
You cannot observe the other agents' choices for this round, and you
cannot communicate before choosing.


Task information:
context_note: Subject: {subject}
{ident}


Make your choice for this round based on the information available.
Your final answer must be a single JSON object, either {{"action":"A"}}
or {{"action":"B"}}, with no explanation."""


def stratum_map(ids, seed):
    """identifier -> stratum, a MAP and never a draw. Amendment 6, fire 348.

    Exactly len(ids)/4 identifiers per stratum, identical in every process,
    independent of the order in which identifiers are collected, reproducible
    from the seed alone. REFUSES if the result is not balanced, because an
    unbalanced map is the failure this exists to prevent and a silent one is
    how arm 1 was collected.
    """
    perm = list(range(len(ids)))
    random.Random(seed + 7).shuffle(perm)
    m = {ids[idx]: i % 4 for i, idx in enumerate(perm)}
    check_strata(m, ids)
    return m


def check_strata(m, ids):
    """The guard, factored out ON PURPOSE so a test can reach it.

    Round-robin dealing cannot produce an unbalanced map, so leaving the check
    inside `stratum_map` made it unreachable: deleting it left the selftest
    GREEN, which is ruler 9 of this project (a check that cannot fail is not a
    check) wearing defence-in-depth's clothes. It exists for a FUTURE map
    construction, so the test calls it directly with a map built to be wrong.
    """
    bal = collections.Counter(m.values())
    if len(ids) % 4 == 0 and len(set(bal.values())) > 1:
        raise SystemExit(f"REFUSING: stratum map is not balanced: {dict(bal)}. "
                         f"The four strata are the only control for an A/B-label "
                         f"or line-order bias; an unbalanced map makes that bias "
                         f"indistinguishable from a rule.")
    if len(m) != len(ids):
        raise SystemExit(f"REFUSING: stratum map covers {len(m)} of {len(ids)} "
                         f"identifiers -- duplicate identifiers in the arm.")


def build(ident_line, q_str, stratum):
    """stratum 0..3 = (which label means participate) x (which line comes first)."""
    part_label = "A" if stratum % 2 == 0 else "B"
    other = "B" if part_label == "A" else "A"
    pline = f"{part_label}: participate"
    oline = f"{other}: do not participate"
    first, second = (pline, oline) if stratum < 2 else (oline, pline)
    return PROMPT.format(line1=first, line2=second, q=q_str, subject=SUBJECT,
                         ident=ident_line), part_label


def call(prompt, thinking, retries=6):
    # 4096 was not enough: half the smoke-test calls hit MAX_TOKENS mid-reasoning
    # and returned no JSON at all. The thinking traces are also the EVIDENCE
    # here -- Gemini exposes them, which the paper's closed models did not --
    # so they are kept whole rather than truncated.
    cfg = {"maxOutputTokens": 16384 if thinking else 64, "temperature": 1.0}
    if not thinking:
        cfg["thinkingConfig"] = {"thinkingBudget": 0}
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": cfg}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(URL, data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as fh:
                d = json.load(fh)
            c = d["candidates"][0]
            txt = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
            return txt, c.get("finishReason", "")
        except urllib.error.HTTPError as e:
            full = e.read().decode(errors="replace")   # NOT truncated -- see below
            raw = full[:400]
            # A 429 has TWO meanings needing opposite handling, and fire 332
            # measured that THE ENGLISH MESSAGE CANNOT TELL THEM APART. A 5-RPM
            # per-minute limit and a daily project limit both say, verbatim,
            # "You exceeded your current quota, please check your plan and billing
            # details". Fire 331 classified on that string and therefore aborted
            # instantly on a transient limit -- and mis-diagnosed the whole block
            # as a dead daily quota. The previous code also did e.read()[:400],
            # which truncated the body BEFORE the fields that actually decide it,
            # so the right answer was structurally invisible.
            # The deciding fields, measured against a live 429:
            #   details[].QuotaFailure.violations[].quotaId
            #       "GenerateRequestsPerMinutePerProjectPerModel-FreeTier" -> transient
            #       ...PerDay...                                           -> dead
            #   details[].RetryInfo.retryDelay  e.g. "46s"  -> how long, from the API
            kind, delay = classify_429(full)
            # Put the DECIDING fields at the front of the stored string. Fire 332:
            # the row used to keep only the first 160 bytes of prose, so the verdict
            # in the file could not be audited against the evidence for it -- the
            # same defect as the truncated read, one layer up.
            tag = f"kind={kind} ids={quota_ids(full)} delay={delay}"
            if e.code == 429 and kind == "day":
                note_day_exhausted(KEYS[KEY_IDX][0] if KEYS else "?", delay, full)
                # A daily exhaustion is fatal for THIS key, not for the run --
                # another project may still have allowance. Rotate and retry.
                if rotate_key() and a < retries - 1:
                    continue
                return f"__HTTP429_QUOTA__ {tag} || {raw[:160]}", "QUOTA"
            if e.code == 429 and kind == "minute" and a < retries - 1:
                # Obey the API's own number rather than a guess of mine.
                time.sleep(min(delay or 30, 75) + 1.0); continue
            if e.code == 429 and kind == "unknown" and a < retries - 1:
                time.sleep(min(delay or 30, 75) + 1.0); continue
            if e.code == 429 and kind == "unknown":
                # Conservative: an unreadable 429 after all retries is treated as
                # dead, which keeps fire 331's protection, but the body is kept so
                # the next me can see what it actually said.
                return f"__HTTP429_UNKNOWN__ {tag} || {raw[:300]}", "QUOTA"
            if e.code in (503, 500) and a < retries - 1:
                time.sleep(4 * (a + 1)); continue
            return f"__HTTP{e.code}__ " + raw[:200], "ERR"
        except Exception as e:
            if a < retries - 1:
                time.sleep(3); continue
            return f"__EXC__ {e}", "ERR"
    return "__FAIL__", "ERR"



def quota_ids(full):
    """Every quotaId in a 429 body, so a stored verdict carries its own evidence."""
    return re.findall(r'"quotaId"\s*:\s*"([^"]*)"', full) or ["<none>"]


def classify_429(full):
    """Decide what a Gemini 429 MEANS, from its structured fields, never its prose.

    Returns (kind, delay_seconds) where kind is "minute" (transient -- a
    per-minute/per-second rate limit), "day" (a daily project quota that will not
    recover in seconds), or "unknown" (nothing parseable).

    Measured against a live 429, fire 332: quotaId
    "GenerateRequestsPerMinutePerProjectPerModel-FreeTier", quotaValue "5",
    retryDelay "46s" -- carrying the SAME English message as a daily exhaustion.
    """
    delay = None
    m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', full)
    if m:
        delay = float(m.group(1))
    else:
        m = re.search(r'retry in (\d+(?:\.\d+)?)s', full)
        if m:
            delay = float(m.group(1))
    ids = re.findall(r'"quotaId"\s*:\s*"([^"]*)"', full)
    blob = " ".join(ids)
    if re.search(r'PerDay|Daily', blob, re.I):
        return "day", delay
    if re.search(r'PerMinute|PerSecond|PerMin\b', blob, re.I):
        return "minute", delay
    return "unknown", delay


def parse(txt, part_label):
    """-> 1 participate, 0 not, None unparseable. Reads the LAST json object so a
    thinking preamble cannot be mistaken for the answer."""
    best = None
    for i in range(len(txt)):
        if txt[i] == "{":
            for j in range(len(txt), i, -1):
                try:
                    o = json.loads(txt[i:j])
                except Exception:
                    continue
                if isinstance(o, dict) and "action" in o:
                    best = o
                break
    if best is None:
        return None
    a = str(best["action"]).strip().upper()
    if a == part_label:
        return 1
    if a in ("A", "B"):
        return 0
    if "participate" in a.lower():
        return 0 if "not" in a.lower() or "do not" in a.lower() else 1
    return None



# ---------------------------------------------------------------- resume
def load_prior(outpath, ids, resume, force):
    """Return (rows_already_banked, identifiers_still_to_collect).

    WHY THIS EXISTS. The free-tier daily cap is ~20-25 calls per model per project
    (measured on three models, fire 332), and an arm is 64 calls. So an arm is
    collected over several days -- and the old runner started `rows = []` and wrote
    the file from scratch, which means day two SILENTLY DESTROYED day one. Same
    footgun as tools.py overwriting its own panel baseline.

    Two refusals, both deliberate:
      * a non-empty output file without --resume is a refusal, not an overwrite;
      * a resume whose stored rows name a DIFFERENT model is a refusal, because the
        multi-day design is only valid with the model pinned, and a note saying
        "pin the model" is not a mechanism.
    """
    if not os.path.exists(outpath) or os.path.getsize(outpath) == 0:
        return [], list(ids)
    prior = json.load(open(outpath))
    if not prior:
        return [], list(ids)
    if not resume:
        if not force:
            sys.exit(f"REFUSING: {outpath} already holds {len(prior)} answers. Pass "
                     f"--resume to continue that arm, or --force to throw it away. "
                     f"(The daily cap means a discarded partial is days of quota.)")
        print(f"--force: discarding {len(prior)} banked answers in {outpath}")
        return [], list(ids)
    # An UNSTAMPED row is not evidence of agreement. The first version of this check
    # filtered None out of the set, so a file written before the stamp existed would
    # resume onto any model at all and say nothing. That is the same shape as a gate
    # that cannot fail.
    if any(not r.get("model") for r in prior):
        sys.exit(f"REFUSING to resume: {outpath} contains rows with no `model` field, "
                 f"so the pinning cannot be checked. Stamp them from the collection "
                 f"record first.")
    seen_models = {r.get("model") for r in prior}
    if seen_models != {MODEL}:
        sys.exit(f"REFUSING to resume: {outpath} was collected on {sorted(seen_models)} "
                 f"and this run is {MODEL}. The design pins the model across days. "
                 f"Set GEM_MODEL to the stored one, or start a new arm file.")
    done = {r["id"] for r in prior if r.get("chose") is not None}
    todo = [h for h in ids if h not in done]
    # drop any unparsed rows for identifiers we are about to retry
    rows = [r for r in prior if r.get("chose") is not None]
    return rows, todo


def _selftest():
    """Exercise the refusals on temp files. Spends no quota."""
    import tempfile, subprocess
    ok = True
    d = tempfile.mkdtemp()
    f = os.path.join(d, "a.json")
    ids = ["aaa", "bbb", "ccc"]

    def chk(name, cond):
        nonlocal ok
        print(f"  {'pass' if cond else 'FAIL'}  {name}")
        ok &= bool(cond)

    # 1. no file -> everything to do
    r, todo = load_prior(f, ids, resume=False, force=False)
    chk("empty path: 0 banked, 3 to do", (r, todo) == ([], ids))

    # 2. non-empty + no --resume -> refuse (SystemExit)
    json.dump([{"id": "aaa", "chose": 1, "model": MODEL}], open(f, "w"))
    try:
        load_prior(f, ids, resume=False, force=False)
        chk("non-empty without --resume REFUSES", False)
    except SystemExit:
        chk("non-empty without --resume REFUSES", True)

    # 3. --resume -> skips the done one
    r, todo = load_prior(f, ids, resume=True, force=False)
    chk("--resume banks 1 and leaves 2", len(r) == 1 and todo == ["bbb", "ccc"])

    # 4. model mismatch -> refuse
    json.dump([{"id": "aaa", "chose": 1, "model": "some-other-model"}], open(f, "w"))
    try:
        load_prior(f, ids, resume=True, force=False)
        chk("model mismatch REFUSES", False)
    except SystemExit:
        chk("model mismatch REFUSES", True)

    # 5. unparsed rows are retried, not banked
    json.dump([{"id": "aaa", "chose": None, "model": MODEL},
               {"id": "bbb", "chose": 0, "model": MODEL}], open(f, "w"))
    r, todo = load_prior(f, ids, resume=True, force=False)
    chk("unparsed row is retried", len(r) == 1 and todo == ["aaa", "ccc"])

    # 6. --force throws it away
    json.dump([{"id": "aaa", "chose": 1, "model": MODEL}], open(f, "w"))
    r, todo = load_prior(f, ids, resume=False, force=True)
    chk("--force discards and restarts", (r, todo) == ([], ids))

    # 7. complete file -> nothing to do
    json.dump([{"id": h, "chose": 1, "model": MODEL} for h in ids], open(f, "w"))
    r, todo = load_prior(f, ids, resume=True, force=False)
    chk("complete arm leaves nothing to do", len(r) == 3 and todo == [])

    # --- Amendment 6: the stratum MAP (fire 348)
    ids64 = rules.designed_identifiers(64, 1/3, seed=331)
    m1 = stratum_map(ids64, 331)
    bal = collections.Counter(m1.values())
    chk("stratum map is exactly balanced 16/16/16/16",
        sorted(bal.values()) == [16, 16, 16, 16])
    chk("stratum map is identical in a second process",
        stratum_map(ids64, 331) == m1)
    # THE REGRESSION TEST, against the observed failure rather than against an
    # idea of it: collect the arm in the SAME four batches arm 1 was collected
    # in (20 / 20 / 21 / 3 calls across four days, each a fresh process) and
    # check the strata that come out are balanced. The old code -- an RNG seeded
    # per process, drawn inside the loop -- gives 29/17/15/3 here, which is what
    # it actually gave. The first version of this check compared a map built
    # from a REVERSED identifier list and had a tautology for its second clause,
    # so it could not fail. Ruler 9 of this project, again: a check that cannot
    # fail is not a check.
    def _multiday(batches, old):
        got, pos = [], 0
        for b in batches:
            rng_b = random.Random(331 + 1)          # a fresh process each day
            for _ in range(b):
                h = ids64[pos]; pos += 1
                got.append(rng_b.randrange(4) if old else stratum_map(ids64, 331)[h])
        return collections.Counter(got)
    chk("resumed over 4 days the map stays balanced",
        sorted(_multiday([20, 20, 21, 3], old=False).values()) == [16, 16, 16, 16])
    chk("...and the OLD per-process RNG does not (the observed 29/17/15/3)",
        sorted(_multiday([20, 20, 21, 3], old=True).values()) != [16, 16, 16, 16])
    chk("every identifier gets a stratum", len(m1) == 64)
    chk("A/B label is split 32/32 by the map",
        sum(1 for v in m1.values() if v % 2 == 0) == 32)
    chk("line order is split 32/32 by the map",
        sum(1 for v in m1.values() if v < 2) == 32)
    try:
        stratum_map(ids64 + [ids64[0]], 331)   # a duplicate identifier
        chk("a duplicate identifier REFUSES", False)
    except SystemExit:
        chk("a duplicate identifier REFUSES", True)
    # the guard itself, reached directly -- round-robin dealing cannot build an
    # unbalanced map, so this is the only way the refusal is ever exercised.
    try:
        check_strata({h: (0 if i < 40 else 1) for i, h in enumerate(ids64)}, ids64)
        chk("an UNBALANCED map REFUSES", False)
    except SystemExit:
        chk("an UNBALANCED map REFUSES", True)
    try:
        check_strata(stratum_map(ids64, 331), ids64)
        chk("a balanced map passes the guard", True)
    except SystemExit:
        chk("a balanced map passes the guard", False)

    # 8. an UNSTAMPED row must refuse -- the first version of the model check
    #    filtered None out and passed silently.
    json.dump([{"id": "aaa", "chose": 1}], open(f, "w"))
    try:
        load_prior(f, ids, resume=True, force=False)
        chk("unstamped row REFUSES", False)
    except SystemExit:
        chk("unstamped row REFUSES", True)

    # ---- the day window, fire 347. ----
    # SYNTHETIC key list on purpose. The first version of these tests used the real
    # KEYS, and this box has exactly ONE key, so the case that actually matters --
    # "one key is unrecorded, therefore do not block" -- SKIPPED ITSELF silently,
    # and a break that deleted that protection passed all nine checks. A test that
    # disappears on the machine it runs on is worse than no test.
    global QSTATE, KEYS
    real_qstate, real_keys = QSTATE, KEYS
    QSTATE = os.path.join(d, "q.json")
    KEYS = [("~/fakeA", "AIzaFAKEA"), ("~/fakeB", "AIzaFAKEB")]
    try:
        # 9. KNOWN ANSWER, through the real function: the 429 we measured on
        #    2026-10-17T07:07:04Z carried delay=60775.0s. That is 23:59:59Z the same
        #    day -- the UTC calendar day -- and NOT midnight MST, which every file in
        #    this project claimed until now.
        seen = datetime.datetime.fromisoformat("2026-10-17T07:07:04+00:00")
        got = note_day_exhausted("~/fakeA", 60775.0, now=seen)
        rec = _qload()[_qkey("~/fakeA")]
        chk("measured 429 -> 2026-10-17T23:59:59Z (the UTC day, not midnight MST)",
            got.isoformat(timespec="seconds") == "2026-10-17T23:59:59+00:00"
            and rec["reset_utc"] == "2026-10-17T23:59:59+00:00"
            and rec["source"] == "RetryInfo")

        now = datetime.datetime.now(datetime.timezone.utc)
        future = (now + datetime.timedelta(hours=3)).isoformat(timespec="seconds")
        later = (now + datetime.timedelta(hours=9)).isoformat(timespec="seconds")
        past = (now - datetime.timedelta(hours=3)).isoformat(timespec="seconds")
        labels = [l for l, _ in KEYS]

        # 10. no record at all -> never blocks
        json.dump({}, open(QSTATE, "w"))
        chk("no record -> not blocked", day_window_block(now) is None)

        # 11. one key recorded, one UNKNOWN -> not blocked; the unknown one may pay
        json.dump({_qkey(labels[0]): {"reset_utc": later}}, open(QSTATE, "w"))
        chk("one key recorded, one unknown -> not blocked",
            day_window_block(now) is None)

        # 12. every key recorded in the future -> blocked, at the EARLIEST reopen
        json.dump({_qkey(labels[0]): {"reset_utc": future},
                   _qkey(labels[1]): {"reset_utc": later}}, open(QSTATE, "w"))
        b = day_window_block(now)
        chk("all keys inside window -> blocked at the earliest reopen",
            b is not None and b.isoformat(timespec="seconds") == future)

        # 13. an elapsed window on ANY key does not block
        json.dump({_qkey(labels[0]): {"reset_utc": past},
                   _qkey(labels[1]): {"reset_utc": later}}, open(QSTATE, "w"))
        chk("elapsed window -> not blocked", day_window_block(now) is None)

        # 14. garbage fails OPEN -- a wasted probe costs one call, a false block
        #     costs a whole day of collection.
        json.dump({_qkey(l): {"reset_utc": "not a date"} for l in labels},
                  open(QSTATE, "w"))
        chk("unparseable reset fails open", day_window_block(now) is None)

        # 15. no RetryInfo -> next 00:00Z, and the row SAYS the number was assumed
        os.remove(QSTATE)
        r = note_day_exhausted(labels[0], None,
                               now=datetime.datetime.fromisoformat(
                                   "2026-10-17T07:07:04+00:00"))
        rec = _qload()[_qkey(labels[0])]
        chk("missing RetryInfo -> next 00:00Z, marked assumed",
            r.isoformat(timespec="seconds") == "2026-10-18T00:00:00+00:00"
            and rec["source"] == "assumed-next-0000Z")

        # 16. the model is part of the key: a window recorded for another model
        #     must not block this one. The quota is per project PER MODEL.
        json.dump({f"some-other-model|{l}": {"reset_utc": later} for l in labels},
                  open(QSTATE, "w"))
        chk("a window for a different model does not block this one",
            day_window_block(now) is None)

        # 17. THE ROUND TRIP, both directions. Test 16 alone is satisfied trivially
        #     by a build that drops MODEL from the state key entirely -- measured:
        #     that break passed every other check. The quota is per project PER
        #     MODEL, so a window written while on model A must block A and must NOT
        #     block B, and only asserting BOTH pins it.
        real_model = MODEL
        try:
            os.remove(QSTATE)
            globals()["MODEL"] = "model-A"
            for l in labels:
                note_day_exhausted(l, 3600.0, now=now)
            blocked_A = day_window_block(now) is not None
            globals()["MODEL"] = "model-B"
            blocked_B = day_window_block(now) is not None
            chk("a window blocks its OWN model and only its own",
                blocked_A and not blocked_B)
        finally:
            globals()["MODEL"] = real_model
    finally:
        QSTATE, KEYS = real_qstate, real_keys
    return ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", default="1/3")
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--seed", type=int, default=331)
    ap.add_argument("--out", default=None)
    ap.add_argument("--sleep", type=float, default=1.2)
    ap.add_argument("--bucket5", action="store_true",
                    help="ARM 4 (Amendment 7): draw identifiers whose LEADING HEX DIGIT "
                         "is 5 (value fraction in [0.3125,0.375)), the only region where "
                         "the threshold rule and a leading-digit heuristic disagree. "
                         "Balanced 16 below q / 16 at-or-above, residue 8/8 within each.")
    ap.add_argument("--random-draw", action="store_true",
                    help="add a random_draw field with no usage instruction (P5/paper fix)")
    ap.add_argument("--resume", action="store_true",
                    help="APPEND to an existing answers file, skipping identifiers already "
                         "answered. The free-tier daily cap is ~20-25 calls per model per "
                         "project, so an arm of 64 takes several days; without this the "
                         "second day DESTROYS the first. Refuses if the stored model "
                         "differs from the current one -- the design pins the model.")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a non-empty output file. Never pass this to a file "
                         "you want to keep; use --resume.")
    ap.add_argument("--anyway", action="store_true",
                    help="ignore the recorded window and probe keys as usual")
    ap.add_argument("--when", action="store_true",
                    help="print the measured day-window state and exit; spends nothing")
    ap.add_argument("--selftest", action="store_true",
                    help="exercise the resume/refuse logic on temp files. Spends no quota.")
    a = ap.parse_args()
    if a.selftest:
        print("run_gemini.py --selftest: resume/refuse logic (no API calls)")
        sys.exit(0 if _selftest() else "SELFTEST FAILED -- do not collect with this build")
    if a.when:
        st = _qload()
        now = datetime.datetime.now(datetime.timezone.utc)
        print(f"model={MODEL}   now={now.isoformat(timespec='seconds')}")
        for label, _k in KEYS:
            rec = st.get(_qkey(label))
            if not rec:
                print(f"  {label:16s} no day-429 on record for this model")
                continue
            r = datetime.datetime.fromisoformat(rec["reset_utc"])
            state = "OPEN" if r <= now else f"closed for {str(r-now).split('.')[0]}"
            print(f"  {label:16s} window reopens {r.isoformat(timespec='seconds')} "
                  f"({r.astimezone().strftime('%-I:%M %p %Z')})  [{state}]  "
                  f"src={rec.get('source')} seen={rec.get('seen_utc')}")
        blk = day_window_block(now)
        print("VERDICT:", ("inside a window until "
              + blk.isoformat(timespec='seconds')
              + " -- ADVISORY ONLY: collect anyway, the first task call is the probe")
              if blk else "no window on record -- probe keys as usual")
        sys.exit(0)
    num, den = (int(x) for x in a.q.split("/"))
    q = num / den
    if a.bucket5:
        ids = rules.bucket5_identifiers(a.n, q, seed=a.seed)
        print(f"ARM 4 (--bucket5): {a.n} identifiers with leading hex digit 5, "
              f"{sum(1 for h in ids if rules.threshold_predicts(h,q))} below q. "
              f"Decision rule registered in PREREGISTRATION.md Amendment 7 (G7-G10).")
    else:
        ids = rules.designed_identifiers(a.n, q, seed=a.seed)
    rng = random.Random(a.seed + 1)
    # --- AMENDMENT 6 (fire 348). The stratum used to be `rng.randrange(4)` drawn
    # INSIDE the collection loop, from an RNG seeded once per PROCESS. With
    # --resume, every fire is a new process that re-seeds and then applies the
    # SAME opening sequence of draws to a DIFFERENT subset of identifiers. Arm 1
    # was collected over four days (20 / 20 / 21 / 3 calls) and 63 of its 64
    # strata match a fresh Random(332) restarted per batch -- chance would be
    # 0.25. Result: strata 29/17/15/3 instead of 16 each, and 46 of 64 calls had
    # "B" meaning participate instead of 32. The cairn says in writing that the
    # four strata are not decoration: without them an "always answer A" bias is
    # indistinguishable from a rule. In arm 1 the bias is there (0.667 vs 0.413
    # participation by label) and the control that should have balanced it away
    # was absent. The resume mechanism built in fire 345 to stop one footgun
    # silently created another.
    #
    # The fix is a MAP, not a draw: shuffle the identifier INDICES once with a
    # fixed seed, then deal strata round-robin. Exactly n/4 per cell, identical
    # for every process, independent of collection order, and reproducible from
    # the seed alone. A note saying "pin the strata" is not a mechanism.
    STRATUM = stratum_map(ids, a.seed)
    outpath = a.out or (f"answers_q{den}_{'think' if a.thinking else 'nothink'}"
                        f"{'_draw' if a.random_draw else ''}.json")
    # FIRE 332: probe keys before spending a single task call. "A key exists" is
    # not "there is access"; only a probe is access. Announce which project is
    # paying, so the run's own log says what served it.
    print(f"model={MODEL}  candidates={[l for l,_ in KEYS]}", flush=True)
    # THE WINDOW IS AN UPPER BOUND, NOT A GATE -- measured, fire 347, ten minutes
    # after the opposite was coded. The first version of this exited here rather
    # than spend a call. Then a real task call went through at 19:05:11Z inside a
    # window whose own RetryInfo said it was shut until 23:59:59Z, and banked a row.
    # Both 429s of that day point at 00:00Z and requests still trickle past the cap
    # for reasons one observation cannot name. So: never refuse on the record.
    # What the record IS good for is skipping the 2-token probe -- a probe costs the
    # same one request as a task call and cannot bank an answer, so inside a known
    # window THE FIRST REAL CALL IS THE CHEAPEST POSSIBLE PROBE.
    blk = day_window_block()
    if blk is not None and not a.anyway:
        print(f"  inside a recorded day window until {blk.isoformat(timespec='seconds')}"
              f" ({blk.astimezone().strftime('%-I:%M %p %Z')}) -- that is an UPPER BOUND,"
              f" so collecting anyway and letting the first task call be the probe.",
              flush=True)
        sel = adopt_first_key()
    else:
        sel = select_key()
    if sel is None:
        sys.exit("NO KEY HAS QUOTA -- every candidate project is daily-exhausted. "
                 "Not collecting. This is a stuck, and it is reportable as one.")
    print(f"using key {sel} ({_fp(API_KEY)})", flush=True)
    rows, ids = load_prior(outpath, ids, a.resume, a.force)
    if not ids:
        print(f"nothing to do: {outpath} already holds {len(rows)} answers for every "
              f"identifier in this arm.")
        sys.exit(0)
    print(f"collecting {len(ids)} of {a.n} (already banked: {len(rows)})", flush=True)
    t0 = time.time()
    hard_errors = 0
    for k, h in enumerate(ids):
        ident = f"agent_id: {h}"
        draw = None
        if a.random_draw:
            draw = round(rng.random(), 6)
            ident += f"\nrandom_draw: {draw}"
        stratum = STRATUM[h]          # Amendment 6: a map, never a draw
        prompt, pl = build(ident, a.q, stratum)
        serving = _fp(API_KEY)
        txt, fin = call(prompt, a.thinking)
        chose = parse(txt, pl)
        rows.append({"id": h, "q": a.q, "thinking": a.thinking, "stratum": stratum,
                     "model": MODEL,
                     "utc": datetime.datetime.now(datetime.timezone.utc)
                             .isoformat(timespec="seconds"),
                     "participate_label": pl, "raw": txt, "finish": fin,
                     "key": serving,
                     "chose": chose, "random_draw": draw,
                     "vf": rules.value_fraction(h),
                     "threshold": rules.threshold_predicts(h, q),
                     "residue": rules.residue_predicts(h, q)})
        # Write after EVERY call. Fire 331 killed a run at 16/64 and lost all of it,
        # because the file was only written at the end. A partial file is also how
        # the next me can see an error rate without re-spending quota.
        json.dump(rows, open(outpath, "w"), indent=1)
        if (k + 1) % 16 == 0:
            ok = sum(1 for r in rows if r["chose"] is not None)
            print(f"  {k+1}/{len(ids)}  parsed {ok}  "
                  f"participated {sum(r['chose'] or 0 for r in rows)}  "
                  f"{time.time()-t0:.0f}s", flush=True)
        if fin == "QUOTA":
            print(f"ABORTING at {k+1}/{len(ids)}: the API reports its QUOTA is "
                  f"exhausted, which does not recover in seconds. Nothing further "
                  f"will be sent. Partial data is in {outpath}.", flush=True)
            break
        if txt.startswith("__HTTP") or txt.startswith("__EXC__") or txt == "__FAIL__":
            hard_errors += 1
        # ABORT EARLY. A run whose parse rate cannot reach 90% is VOID by the
        # pre-registration, so grinding through the remaining calls only burns
        # quota that the next attempt needs. 12 hard errors out of 64 makes 90%
        # unreachable.
        if hard_errors > 6 and hard_errors > 0.25 * (k + 1):
            print(f"ABORTING at {k+1}/{len(ids)}: {hard_errors} hard transport "
                  f"errors ({hard_errors/(k+1):.0%}). This run cannot reach a 90% "
                  f"parse rate, so it would be VOID. Partial data is in {outpath}.",
                  flush=True)
            break
        time.sleep(a.sleep)
    json.dump(rows, open(outpath, "w"), indent=1)
    ok = sum(1 for r in rows if r["chose"] is not None)
    print(f"wrote {outpath}  ({len(rows)} sent, {ok} parsed, "
          f"{hard_errors} transport errors)")

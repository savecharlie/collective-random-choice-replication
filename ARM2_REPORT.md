# Arm 2 — the reasoning arm   (answers35_q3_think.json, gemini-3.5-flash, n=64)

## Registered quantities (same three analyse.py scores)
participation rate   0.4688   (30/64)
E_threshold          +0.8750
E_residue            +0.1250

## The 2x2 (post-hoc)
threshold predicts participate: 29 participated, 3 did not
threshold predicts abstain    : 1 participated, 31 did not
Fisher exact two-sided p = 1.965e-13

## The rate is NOT the test, and this arm proves it (post-hoc)
The designed identifier set is 0.500 threshold-yes by construction,
so a PERFECT threshold-follower participates at 0.500 on this set, not
at q = 0.333. Observed 0.4688. A scorer that compared the rate to q
would read this arm as over-participation (p=0.0168)
when it is near-exact rule-following. Arm 1's rate was 0.484 — within noise of
this one — and arm 1 had NO identifier dependence. Same rate, opposite mechanism.

## Control: the effect inside each stratum (label x line-order)
  stratum 0 (participate=A, participate-line-first) n=16  E_thr=+0.567  (4/6 vs 1/10)
  stratum 1 (participate=B, participate-line-first) n=16  E_thr=+1.000  (6/6 vs 0/10)
  stratum 2 (participate=A, participate-line-second) n=16  E_thr=+1.000  (9/9 vs 0/7)
  stratum 3 (participate=B, participate-line-second) n=16  E_thr=+0.909  (10/11 vs 0/5)
The effect survives in all four. It is not an A/B-label or line-order artifact.

## The 4 disagreements, and the prediction that FAILED
Prediction before looking: if the model is really comparing a value fraction
to 1/3, its errors should cluster at the boundary. They do not.
  mean |vf - q|, all rows : 0.2421
  mean |vf - q|, error rows: 0.2248
  vf=0.330404  chose=0  stratum=3  closeness-rank 2/64
  vf=0.195351  chose=0  stratum=0  closeness-rank 22/64
  vf=0.081586  chose=0  stratum=0  closeness-rank 40/64
  vf=0.839903  chose=1  stratum=0  closeness-rank 55/64
Ranks are spread across the range, so the disagreements look like a flat ~6.2%
failure rate, not fuzziness near the cut. One of the four IS the second-closest
identifier to q in the whole arm; the other three are not close to anything.
Hypothesis for a later arm, NOT a finding: 3 of 4 disagreements are in
stratum 0, where expectation is 1.0 (binomial p = 0.051 at n=4 errors).

## What this arm CANNOT distinguish (post-hoc, and it is the real limitation)
  threshold: vf < 1/3                    60/64  (93.8%)
  vf < 0.35 (fitted, not a hypothesis)   60/64  (93.8%)
  first hex digit <= 4                   59/64  (92.2%)
  first hex digit <= 5                   59/64  (92.2%)
  first two hex < 0x55                   59/64  (92.2%)
  residue: id mod 3 == 0                 36/64  (56.2%)
Only 4 identifiers separate the threshold rule from a first-hex-digit
proxy (those with first digit 5, i.e. vf in [0.3125, 0.375)), and they split:
  vf=0.319835  chose=1   threshold says 1,  digit<=4 says 0,  digit<=5 says 1
  vf=0.330404  chose=0   threshold says 1,  digit<=4 says 0,  digit<=5 says 1
  vf=0.332184  chose=1   threshold says 1,  digit<=4 says 0,  digit<=5 says 1
  vf=0.356949  chose=0   threshold says 0,  digit<=4 says 0,  digit<=5 says 1
So 'the model computed a value fraction and compared it to q' is the BEST fit
by one row, and is not established over 'the model looked at the leading digit'.

## The arm this names (cheap, decisive)
Arm 4: draw all identifiers with first hex digit 5. Threshold then predicts
participation for the 33.3% of that bucket below 1/3 with a sharp step at
0.3333; digit<=4 predicts none; digit<=5 predicts all. n=32 separates all three
outright. This is a better next experiment than arm 3 because arm 3 (a fair
random draw) tests the RATE, and this arm has just shown the rate cannot
identify the mechanism.

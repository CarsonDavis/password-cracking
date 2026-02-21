# Solved Issues

## L33t Variations Formula Underestimated Attack Space

**Date:** 2026-02-19

### Symptom

Adding "1" to the password "ford.yellow.blue.car" made the estimated crack time go **down** from ~4,000 years to ~2,000 years. A longer, more complex password was rated weaker than a shorter one.

### Root Cause

The l33t estimator matched "car1" as a l33t rendering of "carl" (a common name, rank 62). The zxcvbn-inherited `l33t_variations` formula used a binary sub/not-sub model per position, producing a minimum multiplier of **2**. This gave "carl" a guess count of 62 x 2 = 124, which was cheaper than plain "car" (dictionary rank 261). The DP engine picked this cheaper decomposition.

The binary formula doesn't account for **how many** l33t characters map to each position. An attacker generating l33t variants of "carl" must try all possible renderings:

- c: original + 3 subs (`, {, [) = 4 options
- a: original + 2 subs (@, 4) = 3 options
- r: original only = 1 option
- l: original + 2 subs (1, |) = 3 options
- Total: 4 x 3 x 1 x 3 = **36 variants** (not 2)

### Fix

Replaced `l33t_variations` with a full variant count formula. For each character in the de-l33ted word, multiply by `(1 + number of l33t substitutions for that character)`. This models the actual attacker search space — they must try every l33t rendering of the word.

**Files changed:**
- `packages/crack-time/src/crack_time/estimators/scoring.py` — new `l33t_variations(word, l33t_table)` function
- `packages/crack-time/src/crack_time/estimators/leet.py` — pass `match.word` + global l33t table instead of `match.token` + per-match `sub_table`

### Before / After

| Password | Before (old formula) | After (new formula) |
|----------|---------------------|---------------------|
| "carl" (l33t multiplier) | 2 | 36 |
| "carl" (total guesses) | 124 | 2,232 |
| "password" (l33t multiplier) | 2 | 54 |
| ford.yellow.blue.car | ~4,000 years | ~4,000 years |
| ford.yellow.blue.car1 | ~2,000 years | ~33,000 years |

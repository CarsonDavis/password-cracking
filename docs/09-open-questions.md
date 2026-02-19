# Open Questions & Design Decisions

Unresolved design decisions for the Password Crack-Time Simulator. Questions are drawn from the research phase and original project definition. Resolved items are marked with their resolution.

---

## Resolved

| # | Question | Resolution |
|---|----------|------------|
| R1 | Implementation language? | **Python 3.10+** — All reference tools are Python; direct algorithm reuse. Performance-critical paths can be optimized with Cython or Rust later. |

## Open

### 1. Dictionary size vs. accuracy tradeoff

How large a default wordlist should we bundle? A 30K list (like zxcvbn) keeps the package small but misses many passwords. A 14M list (RockYou) is better but adds 150 MB. Should we tier the dictionaries (small bundled, large downloadable)?

### 2. PCFG/Markov training data

What password corpus should we train on? RockYou is the academic standard but is from 2009. More recent breach data is more representative but raises ethical/legal questions about distribution.

### 3. Bloom filter vs. exact lookup for breach data

A Bloom filter for 600M passwords at 1% false positive rate is ~700 MB. An exact sorted binary file is larger but has zero false positives. Which tradeoff is better for the simulator?

### ~~4. Rule file scope~~ → Resolved

Should we support the full Hashcat rule language (50+ operations) or start with the subset used by best64.rule (~20 operations)? The full language is significantly more engineering effort.

**Resolution:** Start with the subset used by best64.rule (Phase 2, deliverable #8 specifies "at minimum: best64.rule" with ~20 operations: `l, u, c, $X, ^X, r, sXY, DN, iNX, oNX, TN, d, [, ]`). The full Hashcat rule language can be extended incrementally in later phases. See [Implementation Roadmap — Phase 2](07-implementation-roadmap.md) deliverable #8.

### ~~5. Password decomposition conflicts~~ → Resolved

When the DP decomposition and individual estimators disagree (e.g., the DP says the optimal split is "pass" + "word123" but the rule estimator finds "password" + append "123" faster), how do we reconcile?

**Resolution:** The min-auto ensemble already handles this correctly. Rule-based estimation is classified as **whole-password** (see [Estimator Specs — Estimator Classification](05-estimator-specs.md#estimator-classification-segment-level-vs-whole-password)). The final crack time is `min(dp_optimal_guesses, rule_based_guesses, ...)`. If the rule estimator finds "password" + rules faster than the DP's segmented decomposition, the rule estimate wins via the `min()`. No DP modification is needed — the two approaches compete at the top level, not within the DP.

### ~~6. Online vs. offline mode~~ → Resolved

Should the simulator support online mode (rate-limited login attempts, ~100/hour) in addition to offline hash cracking? zxcvbn does; it's simple to add but changes the interpretation significantly.

**Resolution:** Offline only for v1. The entire architecture (hardware tiers, hash rate benchmarks, GPU-based cracking model) is designed around offline hash cracking. Online rate-limited estimation could be added as a separate mode in a future version by simply dividing guess numbers by the rate limit (e.g., 100/hour), but this is out of scope for the initial release.

### 7. Internationalization

Most password data and tooling is English-centric. How much effort should we invest in non-English keyboard layouts, dictionaries, and cultural patterns in the initial release?

### 8. Passwords outside all models

If a password isn't in any dictionary, doesn't match any rule inversion, has zero PCFG probability, and a very high Markov level, brute force becomes the only estimate. Should we report this as "resistant to all modeled attacks; brute force time is X" or try harder to find a pattern?

### 9. Passphrase support

How should we handle multi-word passphrases with separators (e.g., "correct-horse-battery-staple")? The nbvcxz Java tool added separator detection to zxcvbn's approach. Should we implement this in Phase 1 or defer to Phase 3 (PRINCE)?

### 10. Confidence intervals

Should the simulator report confidence intervals for probabilistic estimates (PCFG, Markov, Monte Carlo), or just point estimates? Confidence intervals add complexity but honestly communicate uncertainty.

### ~~11. Scoring thresholds~~ → Resolved

zxcvbn uses fixed guess-count thresholds (10^3, 10^6, 10^8, 10^10) for its 0--4 score. Should we adopt the same thresholds, or should our thresholds be hash-algorithm-aware (since the same guess count means very different things for MD5 vs. bcrypt)?

**Resolution:** Use **time-based thresholds** that automatically scale with hash algorithm and hardware tier. The canonical thresholds are defined in terms of crack time (< 1 minute, < 1 day, < 1 year, < 100 years), and guess-count thresholds are derived dynamically from the effective hash rate. See [Validation Strategy — Strength Rating Scaling](08-validation-strategy.md#strength-rating-scaling-across-hashhardware-combinations) for the scaling formula and examples.

### 12. NIST alignment

NIST SP 800-63B (2024 revision) recommends minimum 8 characters, allowing up to 64, checking against compromised lists, and explicitly advises against arbitrary composition requirements. Should the simulator flag NIST compliance/non-compliance as part of its output?

---

### From PROJECT.md (Original Motivating Questions)

These questions from the original project definition remain the driving use cases:

1. **Passphrase length vs. mutation complexity**: Is adding a 4th word to a passphrase genuinely harder to crack than a 3-word passphrase with a random capitalized letter? What about random punctuation inserted mid-word?
2. **Character randomness vs. word-based passwords**: How do 4 random characters compare to 4 random dictionary words when all attack vectors run in parallel?
3. **Diminishing returns of mutations**: Does leet-speak substitution ("p@ssw0rd") meaningfully increase crack time when rule-based attacks exist specifically to handle this?
4. **Realistic time-to-crack**: Not theoretical entropy, but actual estimated wall-clock time given a defined hardware budget.

---

See also: [Requirements](02-requirements.md) | [Use Cases](03-use-cases.md) | [Architecture](04-architecture.md)

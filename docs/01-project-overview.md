# Project Overview & Research Synthesis

The Password Crack-Time Simulator: what it is, why it exists, and what we learned from researching the space.

---

## The Problem

Every existing password strength tool evaluates from a single attack perspective. zxcvbn decomposes passwords into pattern segments but doesn't model rule-based mangling, Markov chains, or PCFG attacks. Hashcat and John the Ripper are cracking tools, not estimators — they require an actual hash and real GPU time. Academic tools like OMEN or the PCFG cracker each implement one strategy. The CMU guess-calculator-framework comes closest to a multi-strategy approach, but it's a batch research tool from the Python 2.7 era, not a usable library.

No production tool models all realistic attack strategies simultaneously and returns the minimum crack time across all of them.

## The Core Formula

A well-resourced attacker runs every available strategy in parallel. A password falls when *any* strategy reaches it. The effective crack time is:

```
crack_time = min(
    time_breach_lookup,
    time_dictionary,
    time_rule_based,
    time_combinator,
    time_hybrid,
    time_mask,
    time_keyboard_walk,
    time_prince,
    time_pcfg,
    time_markov,
    time_neural,
    time_brute_force
)
```

Each `time_X` is computed as `guess_number_X / hash_rate`, where `hash_rate` depends on the hash algorithm and attacker hardware.

## What the Simulator Produces

Given a password, a hash algorithm, and a hardware profile, the simulator returns:

- **Crack time** (seconds) — the minimum across all modeled attacks
- **Winning attack** — which strategy cracks it fastest
- **Per-strategy breakdown** — guess numbers and times for each attack
- **Strength rating** — categorical score based on crack time thresholds
- **Explanation** — human-readable description of the weakest decomposition

## Motivating Questions

From the [original project definition](../PROJECT.md):

1. **Passphrase length vs. mutation complexity**: Is adding a 4th word to a passphrase genuinely harder to crack than a 3-word passphrase with a random capitalized letter? What about random punctuation inserted mid-word?
2. **Character randomness vs. word-based passwords**: How do 4 random characters compare to 4 random dictionary words when all attack vectors run in parallel?
3. **Diminishing returns of mutations**: Does leet-speak substitution ("p@ssw0rd") meaningfully increase crack time when rule-based attacks exist specifically to handle this?
4. **Realistic time-to-crack**: Not theoretical entropy, but actual estimated wall-clock time given a defined hardware budget.

---

## Cross-Cutting Research Findings

Eight reports across two research phases surfaced several patterns that cut across the entire investigation. Full reports are in the [research directory](research/).

### The Min-Auto Pattern Appears Everywhere

The idea that crack time = minimum across all strategies appears independently in multiple sources:

| Source | How It's Expressed |
|--------|-------------------|
| CMU guess-calculator | "Min-auto ensemble" — recommended mode |
| zxcvbn | DP finds minimum-cost decomposition across all pattern types |
| Password-cracking-techniques report | "effective crack time is the minimum across all parallel attack channels" |
| Ur et al. 2015 | "No single approach dominates"; min-auto significantly outperforms individuals |

This convergence validates our core architecture: compute per-strategy estimates, return the minimum.

### Two Complementary Estimation Approaches

The tools split into two camps for estimating guess numbers:

**Analytical (deterministic):**
- zxcvbn's closed-form formulas (dictionary rank, spatial formula, date formula)
- UChicago's rule inversion (exact position in rule x wordlist enumeration)
- PCFG's precomputed probability-to-rank table
- Brute-force keyspace calculation

**Probabilistic (statistical):**
- CMU's Monte Carlo sampling (empirical CDF from model samples)
- OMEN's level-based approximation (discretized probability bins)
- Neural network probability estimation (model assigns P(password), rank estimated from CDF)

Our simulator uses both: analytical methods where exact computation is feasible (dictionary, rules, brute force, keyboard walks, dates), and probabilistic methods where it's not (Markov, PCFG, neural).

### Hash Algorithm Is the Dominant Variable

Across all reports, the hash algorithm consistently emerges as the single largest factor in crack time:

- MD5 to bcrypt (cost=12): **~114 million times slower** on the same hardware
- MD5 to Argon2id (128 MiB): **~432 million times slower**
- A password taking 1 second to brute-force against MD5 takes ~22 years against bcrypt cost=12

The simulator must make hash algorithm a first-class input. Presenting results without specifying the hash algorithm is meaningless.

### All Reference Implementations Are Python

| Tool | Language |
|------|----------|
| zxcvbn | CoffeeScript/JS (zxcvbn-ts: TypeScript) |
| UChicago analytic | Python 3 |
| CMU guess-calculator | Python (originally 2.7) |
| OMEN | C core, Python wrapper (py_omen) |
| PCFG Cracker | Python 3 |
| Password-Guessing-Framework | Python 3 orchestrator |

This confirms Python as the right implementation language for a research-grade simulator. We can import or adapt algorithms directly.

### Password Decomposition Is the Central Problem

Every tool centers on the same core question: how should a password be decomposed into attackable segments?

- **zxcvbn:** DP finds the minimum-cost segmentation across 7 pattern types
- **PCFG:** Parser decomposes into L/D/S/K/Y tokens, then grammar assigns probability
- **UChicago:** Rule inversion implicitly decomposes into (base_word, transformation)
- **CMU:** Each strategy implies its own decomposition
- **OMEN:** N-gram model implicitly decomposes into overlapping character sequences

Our simulator combines these by running all decomposition methods and selecting the one that gives the attacker the fastest path. The [DP engine](05-estimator-specs.md#dp-decomposition-engine) from zxcvbn provides the framework; the individual estimators provide the match candidates.

---

See also: [Requirements](02-requirements.md) | [Use Cases](03-use-cases.md) | [Architecture](04-architecture.md) | [Research Reports](research/)

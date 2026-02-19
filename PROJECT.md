# Password Crack-Time Simulator

> **Note:** This is the original project definition document, preserved for historical reference. For current documentation, see [`docs/index.md`](docs/index.md).

## Problem Statement

Most password strength estimators are fundamentally flawed because they evaluate passwords from a **single attack perspective**. A tool that assumes dictionary attacks will rate random characters as uncrackable. A tool that measures entropy will underestimate how quickly "correcthorsebatterystaple" falls to a combinator attack. Real attackers don't pick one technique -- they run **every state-of-the-art technique in parallel** and the password falls to whichever one cracks it first.

### The Core Question

> If a well-resourced attacker ran every known cracking technique simultaneously against a given password, how long would it take to crack?

### Specific Questions We Want to Answer

1. **Passphrase length vs. mutation complexity**: Is adding a 4th word to a passphrase genuinely harder to crack than a 3-word passphrase with a random capitalized letter? What about random punctuation inserted mid-word?
2. **Character randomness vs. word-based passwords**: How do 4 random characters compare to 4 random dictionary words when all attack vectors run in parallel?
3. **Diminishing returns of mutations**: Does leet-speak substitution ("p@ssw0rd") meaningfully increase crack time when rule-based attacks exist specifically to handle this?
4. **Realistic time-to-crack**: Not theoretical entropy, but actual estimated wall-clock time given a defined hardware budget.

## Approach: Parallel Attack Simulation

The simulator models the password as being attacked by **all techniques simultaneously**. The crack time is determined by the **fastest technique to find the password** (i.e., the minimum across all attack strategies).

```
crack_time = min(
    brute_force_time,
    dictionary_lookup_time,
    rule_based_time,
    combinator_time,
    mask_time,
    markov_time,
    pcfg_time,
    prince_time,
    neural_time,
    keyboard_walk_time,
    breach_lookup_time,
    hybrid_time,
    ...
)
```

### For Each Attack Technique, We Model

1. **Detection**: Would this technique's search space include this password? (e.g., keyboard walk detector checks if the password follows spatial patterns)
2. **Position in search order**: If the technique would find it, approximately where in its candidate ordering does this password appear? (e.g., "password123" appears early in dictionary+rules; "xK9!mQ2@" appears late)
3. **Throughput**: How many candidates per second can this technique test, given the configured hardware and hash algorithm?
4. **Time**: position / throughput = estimated seconds to crack via this technique

## Attack Techniques to Model

### Tier 1: Instant/Near-Instant (< 1 second)
- **Breach database lookup**: Direct match against known leaked passwords (600M+ in HIBP alone, billions in combined breach data)
- **Common password lists**: Top 10K, 100K, 1M most common passwords

### Tier 2: Fast Attacks (seconds to minutes)
- **Dictionary + rules**: Wordlist (e.g., RockYou) with mangling rules (best64, dive, OneRuleToRuleThemAll). Multiplier: base wordlist size x rule count
- **Mask attacks on short passwords**: Pattern-based brute force for passwords < 8 characters
- **Keyboard walk matching**: Spatial pattern detection and generation via kwprocessor-style approach

### Tier 3: Medium Attacks (minutes to hours)
- **Combinator attacks**: Two-word concatenations from dictionaries
- **PRINCE attack**: Multi-word chaining with probability ordering
- **Hybrid attacks**: Dictionary + mask appending/prepending
- **Markov chain generation**: Statistical character-level generation
- **PCFG generation**: Probabilistic grammar-based candidate generation

### Tier 4: Slow Attacks (hours to days)
- **Extended rule stacking**: Cross-product of multiple rule files
- **Neural/ML generation**: PassGAN, LSTM, transformer-based guessing
- **Policy-aware brute force**: Mask attacks constrained to known password policies

### Tier 5: Exhaustive (days to years+)
- **Full brute force**: Exhaustive character-set search at target length
- **Extended passphrase combinator**: Multi-word combinations from large dictionaries

## Configurable Parameters

### Hardware Configuration
| Parameter | Example Values |
|-----------|---------------|
| GPU model | RTX 4090, RTX 3090, A100, H100 |
| GPU count | 1, 4, 8 |
| Hash algorithm | MD5, SHA-256, bcrypt-10, bcrypt-12, Argon2id |

### Attack Configuration
| Parameter | Description |
|-----------|-------------|
| Wordlist size | Size of primary dictionary (default: RockYou ~14M) |
| Rule sets | Which rule files to apply (best64, dive, OneRule) |
| Breach DB size | Number of unique passwords in breach lookup |
| PCFG training set | What the grammar was trained on |
| Passphrase dictionary | Word list for combinator/PRINCE (e.g., EFF diceware, 7776 words) |

### Attacker Profile Presets
- **Script kiddie**: Single GPU, basic wordlist, best64 rules
- **Competent attacker**: 4x high-end GPUs, large wordlists, multiple rule sets, PRINCE, Markov
- **Professional/Nation-state**: 8+ GPUs or cloud cluster, all techniques, custom training data

## Architecture (Proposed)

```
Input: password string + hardware config + hash algorithm

1. Password Analyzer
   - Decompose password into structural tokens (letters, digits, symbols, words)
   - Check against known patterns (keyboard walks, dates, leet speak, etc.)
   - Identify if it matches dictionary words, common passwords, breach data
   - Detect passphrase structure (word boundaries)

2. Attack Estimators (one per technique)
   Each estimator answers: "How many guesses would my technique need to reach this password?"
   - BruteForceEstimator
   - DictionaryEstimator
   - RuleBasedEstimator
   - CombinatorEstimator
   - MaskEstimator
   - MarkovEstimator
   - PCFGEstimator
   - PRINCEEstimator
   - NeuralEstimator
   - KeyboardWalkEstimator
   - BreachLookupEstimator
   - HybridEstimator
   - ~~PolicyFingerprintEstimator~~ (Dropped: subsumed by the mask estimator, which models policy-constrained brute force via per-position character class keyspace. A dedicated policy fingerprint estimator added minimal value over mask + brute-force estimation.)

3. Hardware Speed Calculator
   - Maps (hash_algorithm, gpu_model, gpu_count) -> hashes/second
   - Accounts for memory-hard function bottlenecks

4. Result Aggregator
   - crack_time[i] = guesses[i] / speed[i] for each technique
   - overall_crack_time = min(crack_time)
   - Reports: which technique wins, runner-up techniques, breakdown
```

## Output Format (Proposed)

```
Password: "correct horse battery staple"
Hash: bcrypt (cost 12)
Hardware: 4x RTX 4090

CRACK TIME ESTIMATE: ~2.3 hours

Breakdown by technique:
  PRINCE (4-word chain)    :  2.3 hours   <-- WINNER
  Combinator (2x2 words)   :  4.1 hours
  Dictionary + rules        : 18.7 days    (not in base wordlist)
  Markov chain              : 47.2 days
  PCFG                      : 89.3 days
  Brute force (27 chars)    : 3.4 x 10^28 years
  Breach lookup             : NOT FOUND

Recommendation: Add a 5th word or insert random characters between words.
```

## Research Inventory

### Existing Prior Research (in this repo)
- `password-cracking-techniques/background.md` -- Catalog of cracking techniques with sources
- `password-strength-estimators/background.md` -- Survey of existing strength estimation tools

### Research In Progress (via deep-research agents)
- [ ] Existing password strength estimators and simulators (comprehensive survey)
- [ ] State-of-the-art cracking techniques (detailed mechanics and modeling approaches)
- [ ] Hardware benchmarks for cracking speed (hash rates by algorithm and GPU)

### Key Existing Tools to Study
| Tool | Approach | Limitation |
|------|----------|------------|
| **zxcvbn** (Dropbox) | Pattern matching + dictionary + keyboard walks | No GPU speed modeling, no PCFG/Markov/neural |
| **CMU guess-calculator-framework** | Simulates multiple cracking algorithms | Academic, not maintained |
| **Passfault** (OWASP) | Pattern decomposition | Outdated, no modern techniques |
| **KeePass quality estimation** | Shannon entropy + pattern penalties | Pure entropy, no attack simulation |
| **CMU password_meter** | Neural network trained on cracking results | Research prototype |
| **OMEN** (RUB-SysSec) | Markov-based ordered password generation | Single technique only |

## Open Questions

1. **How to model PCFG/Markov guess numbers without actually running the generators?** Need analytical approximations or precomputed lookup tables.
2. **How to handle the interaction between techniques?** Some passwords are hard for ALL techniques; others are hard for most but trivial for one.
3. **What's the right granularity for "breach lookup"?** Exact match only, or fuzzy matching with common mutations?
4. **Should we model the attacker's time budget?** (e.g., after 48 hours they give up)
5. **Implementation language?** Python for prototyping, Rust/Go for performance, or web-based (JS/TS) for accessibility?

## Next Steps

1. Review research agent findings when complete
2. Study zxcvbn and CMU guess-calculator-framework implementations in detail
3. Build a prototype of the password analyzer (structural decomposition)
4. Implement the brute force and dictionary estimators first (simplest)
5. Add increasingly sophisticated estimators
6. Validate against known benchmarks (Hive Systems tables, hashcat benchmarks)

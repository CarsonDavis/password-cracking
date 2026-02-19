# Validation Strategy & Output Format

How we validate the simulator's correctness and what its output looks like.

---

## Unit-Level Validation

Each estimator is tested against known-answer passwords where the correct guess number can be computed by hand or by running the reference tool.

| Estimator | Validation Method |
|-----------|------------------|
| Brute force | Compare against Hive Systems tables (known keyspace / known hash rate = known time) |
| Dictionary | Verify rank matches position in actual wordlist file |
| Keyboard walk | Compare against zxcvbn output for same password |
| Rule-based | Run actual Hashcat on a small test set, compare analytic guess numbers |
| PCFG | Run pcfg_guesser.py, compare probability and rank |
| Markov | Run OMEN enumNG, compare level assignment |
| Combinator | Run Hashcat mode 1, verify position |
| Breach lookup | Verify against HIBP API for known breached/unbreached passwords |

## System-Level Validation

Compare full-pipeline output against established references.

| Reference | What We Compare |
|-----------|----------------|
| Hive Systems 2025 tables | Brute-force times for random passwords of various lengths and charsets against bcrypt |
| zxcvbn scores | Our estimate should be <= zxcvbn's (we model more attacks, so we should find faster paths) |
| Actual Hashcat runs | Run Hashcat with dictionary + best64 on a test hash set; compare predicted vs. actual crack order |

**Academic validation:** Reproduce published guessability curves from Ur et al. 2015 and Melicher et al. 2016 to validate implementations against peer-reviewed results.

## Test Case Passwords

Specific passwords with expected winning attack strategy:

| Password | Expected Winner | Why |
|----------|----------------|-----|
| `password` | Dictionary | Rank #1 in most wordlists |
| `P@ssw0rd!` | Rule-based (dictionary + l33t + append) | Common base "password" + l33t + suffix |
| `qwerty123` | Keyboard walk + sequence | Spatial pattern + digit sequence |
| `correcthorsebatterystaple` | Combinator / PRINCE | Four common dictionary words concatenated |
| `Tr0ub4dor&3` | Rule-based (dictionary + l33t) | XKCD's "hard to remember" example |
| `Summer2024!` | Hybrid (dictionary + mask ?d?d?d?d?s) | Common word + year + symbol |
| `8j$kL2!nQ` | Brute force | Truly random; no pattern shortcuts |
| `iloveyou` | Dictionary / breach | Top-10 most common password |
| `1qaz2wsx` | Keyboard walk | Vertical keyboard walk pattern |
| `monkey69` | Dictionary + combinator | Common word + common number |
| `aaaaaa` | Repeat | Single character repeated |
| `01151987` | Date | MMDDYYYY format date |
| `J4m3$_B0nd007` | Rule-based (l33t + semantic) | Leet-speak of "James" + pop culture |
| `abcdefgh` | Sequence | 8-character ascending lowercase sequence |
| `zxcvbnm,.` | Keyboard walk | Bottom-row horizontal walk |
| `dragon` | Dictionary | Common password (RockYou rank ~8) |
| `123456789` | Dictionary / brute force | #1 most common password; also trivial keyspace |
| `X7#kP2$mQ9` | Brute force | Random, no pattern shortcuts |
| `letmein` | Breach + dictionary | Top-20 most common password |
| `baseball1` | Hybrid (dictionary + mask ?d) | Common word + single digit |
| `p@$$w0rd` | Dictionary + l33t | Heavy leet substitution of rank-1 password |

## Validation Rules

**vs. zxcvbn:** Our simulator should always estimate crack time **less than or equal to** zxcvbn's estimate for the same password, because we model more attack strategies. If our estimate is ever *higher* than zxcvbn's, we have a bug (we're missing an attack path that zxcvbn finds).

**vs. Hive Systems:** For truly random passwords of known length and character set, our brute-force estimator should match Hive Systems' published times within a factor of 2x (accounting for their specific hardware setup of 12x RTX 5090).

**Ground-truth Hashcat methodology:**

1. Generate 1,000 test passwords with known properties (dictionary words, rule mutations, random strings, etc.)
2. Hash them with MD5 and bcrypt
3. Run Hashcat with dictionary + best64.rule, record which passwords crack and at what position
4. Compare our analytic guess numbers against actual Hashcat positions
5. Acceptable accuracy: within 10x for rule-based, exact for dictionary

---

## Output Format

### CLI Human-Readable Output

```
$ crack-time estimate "Summer2024!" --hash bcrypt_cost12 --hardware rig_8x_rtx4090

Password:     Summer2024!
Hash:         bcrypt (cost=12)
Hardware:     8x RTX 4090 (10,781 H/s effective)

Crack Time:   ~1.4 hours
Rating:       WEAK (1/4)
Winner:       Hybrid attack (dictionary + mask ?d?d?d?d?s)

Strategy Breakdown:
  Breach lookup:      NOT FOUND
  Dictionary:         "summer" rank 847, guess #847          → 4.7 seconds
  Dictionary+rules:   "summer" + capitalize + $2$0$2$4$!     → 12 minutes
  Hybrid attack:      "Summer" rank 847 × ?d?d?d?d?s (330K) → 1.4 hours   ← WINNER
  Keyboard walk:      NOT DETECTED
  Mask attack:        ?u?l?l?l?l?l?d?d?d?d?s = 309B         → 3.3 years
  PCFG:               L6D4S1, P=2.1e-8, rank ~4.7M          → 7.3 minutes
  Markov (OMEN):      Level 4, ~12M guesses                  → 18.5 minutes
  Brute force:        72^11 = 2.1e20                         → 620M years

Decomposition: ["Summer" (dict #847)] + ["2024!" (hybrid mask ?d?d?d?d?s)]
```

### JSON Output

```json
{
  "password": "Summer2024!",
  "hash_algorithm": "bcrypt_cost12",
  "hardware_tier": "rig_8x_rtx4090",
  "effective_hash_rate": 10781,
  "crack_time_seconds": 5040,
  "crack_time_display": "1.4 hours",
  "rating": 1,
  "rating_label": "WEAK",
  "winning_attack": "hybrid",
  "strategies": {
    "breach_lookup": {"guess_number": null, "applicable": false},
    "dictionary": {"guess_number": 847, "details": {"word": "summer", "rank": 847}},
    "hybrid": {"guess_number": 54340847, "details": {"base": "Summer", "mask": "?d?d?d?d?s"}},
    "brute_force": {"guess_number": 2.1e20, "details": {"cardinality": 72, "length": 11}}
  },
  "decomposition": [
    {"segment": "Summer", "type": "dictionary", "guesses": 1694},
    {"segment": "2024!", "type": "hybrid_mask", "guesses": 330000}
  ]
}
```

### Strength Rating Scale

Adapted from zxcvbn, calibrated to offline bcrypt attacks:

| Rating | Label | Crack Time (offline, bcrypt cost=12, 8 GPUs) | Guess Count |
|--------|-------|----------------------------------------------|-------------|
| 0 | CRITICAL | < 1 minute | < 650K |
| 1 | WEAK | < 1 day | < 930M |
| 2 | FAIR | < 1 year | < 340B |
| 3 | STRONG | < 100 years | < 34T |
| 4 | VERY STRONG | > 100 years | > 34T |

Note: These thresholds are hardware- and hash-dependent. The simulator should allow custom threshold configuration.

---

See also: [Requirements](02-requirements.md) | [Estimator Specs](05-estimator-specs.md) | [Implementation Roadmap](07-implementation-roadmap.md)

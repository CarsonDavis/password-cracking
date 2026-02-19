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

### Edge Case Test Passwords

These edge cases exercise boundary conditions not covered by the standard test passwords above:

| Password | Expected Behavior | Why |
|----------|------------------|-----|
| *(empty string)* | Orchestrator short-circuits before running estimators: return guess_number = 0, crack_time = 0, rating = 0 (CRITICAL) | No work needed to crack an empty password; special-cased because brute-force formula (cardinality^0 = 1) doesn't apply — there's nothing to guess |
| `a` | Brute force, guess_number ≤ 26 | Single character; trivial keyspace |
| `   ` (3 spaces) | Brute force, guess_number = 33^3 = 35,937 | Whitespace-only; spaces are in the special charset (33 chars), so cardinality = 33, not 95 |
| `aB3!` (4 chars) | Brute force, guess_number = 95^4 | Short password, all character classes present |
| `ThisIsAnExtremelyLongPasswordThatGoesOnAndOnForOverOneHundredCharactersJustToTestEdgeCasesInTheSimulatorEngine!!!` | All estimators return a result without timeout or crash; NFR-002 < 2s latency | Stress test for O(n^2) algorithms like dictionary substring matching |
| `密码测试` | Brute force only (no dictionary/pattern matches expected for CJK) | Unicode-only password; tests charset detection |
| `🔒🔑💻🖥️` | Brute force only; charset detection handles multi-byte characters | Emoji password; tests unicode handling |
| `pass\x00word` | Reject or sanitize null bytes; return error or treat as two tokens | Null byte in password; security boundary test |
| `correcthorsebatterystaple` × 4 (100+ chars) | Repeat estimator detects repetition; does not hang | Very long password with repeated structure |

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
Hardware:     8x RTX 4090 (10,059 H/s effective)

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
  "effective_hash_rate": 10059,
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

#### Strength Rating Scaling Across Hash/Hardware Combinations

The guess-count thresholds above are calibrated for `bcrypt cost=12` at `8x RTX 4090` (10,059 H/s effective). When a different hash algorithm or hardware tier is used, the same guess count produces a vastly different crack time. The rating system should **scale thresholds based on the effective hash rate** so that the ratings reflect *time-to-crack*, not raw guess counts.

**Scaling formula:**

```python
def scaled_thresholds(effective_hash_rate: float) -> dict[int, int]:
    """Compute guess-count thresholds for the given effective hash rate.

    The reference thresholds are defined in terms of crack TIME:
      Rating 0 (CRITICAL): < 1 minute
      Rating 1 (WEAK):     < 1 day
      Rating 2 (FAIR):     < 1 year
      Rating 3 (STRONG):   < 100 years
      Rating 4 (VERY STRONG): >= 100 years

    Convert time thresholds to guess counts using: guesses = time × hash_rate
    """
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_DAY = 86_400
    SECONDS_PER_YEAR = 31_557_600  # 365.25 days

    return {
        0: int(effective_hash_rate * SECONDS_PER_MINUTE),       # < 1 minute
        1: int(effective_hash_rate * SECONDS_PER_DAY),          # < 1 day
        2: int(effective_hash_rate * SECONDS_PER_YEAR),         # < 1 year
        3: int(effective_hash_rate * SECONDS_PER_YEAR * 100),   # < 100 years
        # Rating 4: everything above rating 3 threshold
    }

# Example: MD5 on single GPU (164.1 GH/s)
#   Rating 0: < 9.8T guesses     (< 1 minute)
#   Rating 1: < 14,178T guesses  (< 1 day)
#   Rating 4: > 518,000,000T     (> 100 years)
#
# Example: bcrypt cost=12 on 8 GPUs (10,059 H/s)
#   Rating 0: < 604K guesses     (< 1 minute)
#   Rating 1: < 869M guesses     (< 1 day)
#   Rating 4: > 31.7T            (> 100 years)
```

This means the **time-based definitions** (< 1 minute, < 1 day, etc.) are the canonical thresholds, and the guess-count thresholds in the table above are derived values for the reference configuration. The implementation should compute thresholds dynamically from the effective hash rate.

---

## Error Handling Specification

The simulator must handle the following error conditions gracefully:

| Condition | Behavior | Return Value |
|-----------|----------|--------------|
| Empty password (`""`) | Orchestrator short-circuits before estimators: return guess_number = 0, crack_time = 0, rating = 0 (CRITICAL) | Valid `EstimateResult` |
| Whitespace-only password | Treat as a normal password (all special characters); run all estimators | Valid `EstimateResult` |
| Unknown hash algorithm | Raise `ValueError` with message listing supported algorithms | Exception |
| Unknown hardware tier | Raise `ValueError` with message listing supported tiers | Exception |
| Non-string input | Raise `TypeError` with descriptive message | Exception |
| Very long password (100+ chars) | Process normally but enforce a timeout per estimator (NFR-002: < 2s total). If any estimator exceeds its time budget, skip it and log a warning. | Valid `EstimateResult` (may omit slow estimators) |
| Null bytes in password | Strip null bytes before processing and log a warning | Valid `EstimateResult` |
| Non-ASCII / Unicode password | Detect character set; compute cardinality based on observed Unicode blocks. Dictionary matching runs on normalized forms. Keyboard walk detection skips non-keyboard characters. | Valid `EstimateResult` |
| Estimator internal error | Catch exception, log error, return `guess_number = float('inf')` for that estimator. Other estimators continue. | Valid `EstimateResult` |

**Error response format (JSON):**

```json
{
  "error": true,
  "error_type": "ValueError",
  "message": "Unknown hash algorithm 'sha3'. Supported: md5, sha1, sha256, sha512, ntlm, bcrypt_cost5, bcrypt_cost10, bcrypt_cost12, scrypt_default, argon2id_64m_t3, pbkdf2_sha256"
}
```

---

## Batch Mode Summary Statistics

When running in batch mode (`crack-time batch <password-file>`), the output includes per-password results plus aggregate summary statistics (per UC-2):

### Summary Statistics to Compute

| Statistic | Description |
|-----------|-------------|
| Rating distribution | Count and percentage of passwords at each rating level (0-4) |
| Median crack time | Median crack time across all passwords |
| Weakest passwords | Bottom 10 passwords by crack time (sorted ascending) |
| Winning attack distribution | Count of how many passwords each attack type wins for |
| Top weaknesses | Most common pattern types found in the weakest passwords |
| Coverage statistics | How many passwords each estimator was applicable to |

### Batch CLI Output Example

```
$ crack-time batch passwords.txt --hash bcrypt_cost12 --hardware rig_8x_rtx4090

Evaluated: 1,000 passwords
Median crack time: 4.2 hours

Rating Distribution:
  CRITICAL (0):    127 (12.7%)  ████████████▋
  WEAK (1):        341 (34.1%)  ██████████████████████████████████▏
  FAIR (2):        298 (29.8%)  █████████████████████████████▊
  STRONG (3):      156 (15.6%)  ███████████████▌
  VERY STRONG (4):  78 ( 7.8%)  ███████▊

Winning Attack Distribution:
  Dictionary:      287 (28.7%)
  Rule-based:      234 (23.4%)
  Hybrid:          189 (18.9%)
  Keyboard walk:    87 ( 8.7%)
  Brute force:      78 ( 7.8%)
  Breach lookup:    56 ( 5.6%)
  Other:            69 ( 6.9%)

Top 5 Weakest Passwords:
  1. "password"       → < 1 second  (dictionary, rank #1)
  2. "123456"         → < 1 second  (dictionary, rank #2)
  3. "qwerty"         → < 1 second  (keyboard walk)
  4. "iloveyou"       → < 1 second  (dictionary, rank #5)
  5. "admin"          → < 1 second  (dictionary, rank #12)

Top Weakness Patterns:
  - 34.1% contain a common dictionary word
  - 18.9% use dictionary word + digits/symbols suffix
  - 12.7% are exact matches in breach databases
  - 8.7% follow keyboard layout patterns
```

### Batch JSON Output

```json
{
  "total_passwords": 1000,
  "summary": {
    "median_crack_time_seconds": 15120,
    "rating_distribution": {"0": 127, "1": 341, "2": 298, "3": 156, "4": 78},
    "winning_attack_distribution": {"dictionary": 287, "rule_based": 234, "hybrid": 189},
    "top_weaknesses": [
      {"pattern": "dictionary_word", "percentage": 34.1},
      {"pattern": "dict_plus_suffix", "percentage": 18.9}
    ]
  },
  "passwords": [
    {"password": "...", "crack_time_seconds": 0.1, "rating": 0, "winning_attack": "dictionary"},
    ...
  ]
}
```

---

See also: [Requirements](02-requirements.md) | [Estimator Specs](05-estimator-specs.md) | [Implementation Roadmap](07-implementation-roadmap.md)

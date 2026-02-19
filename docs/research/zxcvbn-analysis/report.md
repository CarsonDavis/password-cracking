# zxcvbn: Technical Analysis of Dropbox's Password Strength Estimator

**Date:** 2026-02-15
**Purpose:** Deep technical analysis of zxcvbn internals, focused on extractable design patterns for building a parallel attack simulator.

---

## Executive Summary

zxcvbn models password cracking as a **combinatorial optimization problem**. Rather than measuring entropy or checking rules, it decomposes a password into segments that correspond to real attack strategies (dictionary words, keyboard patterns, dates, etc.), then finds the decomposition that an optimal attacker would discover fastest. The core algorithm is a dynamic programming shortest-path computation over all possible segmentations, where the cost function is the product of per-segment guess counts.

Three design patterns are directly extractable for an attack simulator:

1. **The segmentation-as-shortest-path model** -- decompose any password into segments via DP, minimizing total attacker effort
2. **Per-pattern guess estimation formulas** -- closed-form functions that estimate search space size for each attack type
3. **The omnimatch-then-optimize pipeline** -- generate all possible matches first (over-generate), then let the optimizer choose the best decomposition

The original implementation is ~1,100 lines of CoffeeScript across 7 source files. The USENIX Security 2016 paper by Daniel Lowe Wheeler provides the formal algorithmic framework.

---

## Table of Contents

1. [Codebase Architecture](#1-codebase-architecture)
2. [The Pipeline: How zxcvbn Processes a Password](#2-the-pipeline)
3. [Pattern Matchers (matching.coffee)](#3-pattern-matchers)
4. [Guess Estimation Formulas (scoring.coffee)](#4-guess-estimation-formulas)
5. [The Minimum-Guess Decomposition (scoring.coffee)](#5-the-minimum-guess-decomposition)
6. [Crack Time Estimation (time_estimates.coffee)](#6-crack-time-estimation)
7. [Dictionary and Frequency Data](#7-dictionary-and-frequency-data)
8. [The Wheeler USENIX Security 2016 Paper](#8-the-wheeler-paper)
9. [zxcvbn-ts: Architectural Changes](#9-zxcvbn-ts)
10. [Extractable Design Patterns for an Attack Simulator](#10-extractable-design-patterns)

---

## 1. Codebase Architecture

The original zxcvbn is written in CoffeeScript (compiled to JavaScript). The repository has been stable since approximately 2017.

### Source File Map

| File | Role | Approx. Lines |
|------|------|---------------|
| `src/main.coffee` | Entry point; orchestrates the pipeline | ~50 |
| `src/matching.coffee` | All pattern matchers (7 types) | ~500 |
| `src/scoring.coffee` | Guess estimation + DP decomposition | ~300 |
| `src/time_estimates.coffee` | Guesses-to-crack-time conversion | ~50 |
| `src/feedback.coffee` | User-facing strength suggestions | ~150 |
| `src/frequency_lists.coffee` | Embedded ranked dictionaries (generated) | ~800KB |
| `src/adjacency_graphs.coffee` | Keyboard layout adjacency data | ~200 |
| `data-scripts/build_frequency_lists.py` | Builds compressed frequency data from raw corpora | ~100 |

The compiled JavaScript bundle is approximately 800KB, dominated by the embedded dictionary data.

---

## 2. The Pipeline

`zxcvbn(password, user_inputs=[])` executes four stages:

```
Password
    |
    v
[1. MATCHING]  -- omnimatch(): Run ALL pattern matchers.
    |              Produces a flat array of match objects.
    |              Each match: {pattern, token, i, j, ...metadata}
    |              where i,j are start/end indices into password.
    v
[2. SCORING]   -- most_guessable_match_sequence(): Dynamic programming.
    |              Finds the non-overlapping sequence of matches
    |              covering the full password that MINIMIZES total guesses.
    |              Output: optimal match sequence + guess count.
    v
[3. TIME EST]  -- estimate_attack_times(): Convert guess count
    |              to wall-clock time under 4 attack scenarios.
    v
[4. FEEDBACK]  -- get_feedback(): Generate user-facing suggestions
    |              based on the weakest match in the sequence.
    v
Result Object: {password, guesses, guesses_log10, score (0-4),
                crack_times_seconds, crack_times_display,
                sequence (match objects), feedback}
```

**Key architectural insight:** Matching and scoring are fully decoupled. The matchers over-generate candidates (every possible pattern at every position), and the DP optimizer selects the best decomposition. This clean separation means you can add new pattern matchers without touching the scoring algorithm.

---

## 3. Pattern Matchers

All matchers live in `matching.coffee`. The `omnimatch(password)` function runs every matcher and concatenates results into a single flat array. Each match object contains at minimum:

```javascript
{
  pattern: 'dictionary' | 'spatial' | 'repeat' | 'sequence' | 'date' | 'regex' | 'bruteforce',
  token: 'the matched substring',
  i: start_index,       // inclusive
  j: end_index,         // inclusive
  // ... pattern-specific metadata
}
```

### 3.1 Dictionary Matcher

**What it does:** Checks every substring of the password against ranked frequency dictionaries.

**Algorithm:**
```
For each start position i in [0, n-1]:
  For each end position j in [i, n-1]:
    word = password[i..j].toLowerCase()
    For each dictionary in [passwords, english, names, surnames, tv_film, user_inputs]:
      If word is in dictionary:
        Emit match with rank = dictionary[word]
```

This is O(n^2 * D) where D is the number of dictionaries. Each dictionary is a hash map, so lookup is O(1).

**Match metadata:**
```javascript
{
  pattern: 'dictionary',
  dictionary_name: 'passwords' | 'english_wikipedia' | ...,
  rank: 1523,                    // frequency rank (1 = most common)
  matched_word: 'password',      // the canonical form matched
  reversed: false,               // was it matched backward?
  l33t: false,                   // was l33t substitution used?
  // uppercase tracking fields...
}
```

### 3.2 Reverse Dictionary Matcher

**What it does:** Reverses the password, then runs the dictionary matcher on the reversed version. This catches passwords like "drowssap" (password backward).

The resulting matches have `reversed: true`, which adds a factor of 2 to the guess estimate (the attacker would try both forward and backward).

### 3.3 L33t Substitution Matcher

**What it does:** Detects dictionary words obscured by leetspeak substitutions.

**Substitution table (hardcoded):**
```
a <- [@, 4]
b <- [8]
c <- [(, {, <]
e <- [3]
g <- [6, 9]
i <- [1, !]
l <- [1, |, 7]
o <- [0]
s <- [$, 5]
t <- [+, 7]
x <- [%]
z <- [2]
```

**Algorithm:**
1. Scan the password for characters that appear in the substitution table (as substituted forms)
2. Build a "relevant substitution table" -- only subs that actually appear in the password
3. Generate all possible combinations of de-l33t substitutions (since some characters like `1` can map to either `i` or `l`, all combinations must be tried)
4. For each de-l33ted variant, run the dictionary matcher
5. Record which substitutions were used in the match metadata

**Combinatorial explosion guard:** If the number of possible substitution combinations exceeds some threshold, the implementation caps enumeration to avoid pathological performance on adversarial inputs.

**Match metadata adds:**
```javascript
{
  l33t: true,
  sub: {'@': 'a', '3': 'e'},     // substitutions used
  sub_display: '@ -> a, 3 -> e'
}
```

### 3.4 Spatial (Keyboard) Matcher

**What it does:** Detects keyboard walk patterns like "qwerty", "zxcvbn", "1qaz2wsx".

**Data structures:** Four adjacency graphs are embedded:
- **qwerty** -- standard US QWERTY (~47 keys)
- **dvorak** -- Dvorak layout
- **keypad** -- numeric keypad (0-9, +, -, *, /)
- **mac_keypad** -- Mac numeric keypad variant

Each graph maps every key to its directional neighbors. For qwerty, each key has up to 6 neighbors (arranged by direction). The adjacency entry stores both the unshifted and shifted character for each neighbor position, e.g.:

```javascript
'q': ['`~', null, null, 'wW', 'aA', null]
//    NW     N     NE    E     SE    S
```

**Algorithm:**
```
For each keyboard graph G:
  For each starting position i in password:
    Walk forward from position i:
      At each step, check if password[pos+1] is adjacent to password[pos] in G
      Track: number of turns (direction changes), number of shifted characters
      If not adjacent: stop the walk
      If walk length >= 3: emit a spatial match
```

**Match metadata:**
```javascript
{
  pattern: 'spatial',
  graph: 'qwerty',
  turns: 3,           // number of direction changes in the walk
  shifted_count: 1     // how many characters required shift
}
```

**Key constants computed from the graph:**
- `starting_positions` -- number of keys on the keyboard (~47 for qwerty, 15 for keypad)
- `average_degree` -- average number of non-null neighbors (~4.595 for qwerty, ~5.066 for keypad)

### 3.5 Repeat Matcher

**What it does:** Detects repeated characters or repeated sequences: "aaa", "abcabcabc".

**Algorithm (two-phase):**

**Phase 1 -- Greedy match:** Uses regex `/(.+)\1+/g` to find the longest repeated sequence at each position. This catches multi-character repeats like "abcabc".

**Phase 2 -- Lazy match:** Uses regex `/(.+?)\1+/g` to find the shortest repeating unit. For "aabaab", greedy finds "aab" repeated, lazy finds "a" repeated (different decomposition).

Both are tried, and the one yielding fewer guesses wins.

**Recursive evaluation:** For multi-character base strings, zxcvbn recursively calls itself on the base string to determine its strength. For example, for "batterybattery", it evaluates "battery" independently to get `base_guesses`, then multiplies by the repeat count.

**Match metadata:**
```javascript
{
  pattern: 'repeat',
  base_token: 'abc',       // the repeating unit
  base_guesses: 126,       // guesses for the base token alone
  repeat_count: 3           // how many times it repeats
}
```

### 3.6 Sequence Matcher

**What it does:** Detects character sequences with a constant delta: "abc", "135", "zyx", "97531".

**Algorithm:**
```
For each position i in password:
  For each position j > i:
    delta = ord(password[j]) - ord(password[j-1])
    If delta is consistent across all adjacent pairs in [i..j]:
      If |delta| is 1 or 2 (and length >= 3):
        Emit sequence match
```

Recognizes ascending/descending sequences in digits, lowercase letters, and uppercase letters. The delta must be +1, -1, +2, or -2 (for common skip sequences).

**Match metadata:**
```javascript
{
  pattern: 'sequence',
  sequence_name: 'lower' | 'upper' | 'digits',
  sequence_space: 26 | 26 | 10,  // alphabet size
  ascending: true | false
}
```

### 3.7 Date Matcher

**What it does:** Detects dates in common formats, with or without separators.

**Formats recognized:**
- With separators: `mm/dd/yyyy`, `dd.mm.yyyy`, `yyyy-mm-dd`, and many variations
- Without separators: `mmddyyyy`, `ddmmyy`, `yyyymmdd`, and all orderings of m/d/y

**Algorithm:**
1. Extract candidate date substrings (length 4-8 without separators, 6-10 with separators)
2. For without-separator dates: try all possible splits into 2/3/4 character groups
3. For each split: try all 6 orderings of (month, day, year)
4. Validate: month in 1-12, day in 1-31, year in plausible range
5. Prefer 4-digit years over 2-digit years
6. Among multiple valid parses, prefer the one closest to the reference year

**Two-digit year handling:** Maps 0-99 to either 1900-1999 or 2000-2099 depending on which is closer to the reference year.

**Match metadata:**
```javascript
{
  pattern: 'date',
  separator: '/' | '-' | '.' | '',
  year: 1987,
  month: 6,
  day: 15
}
```

### 3.8 Regex Matcher

**What it does:** Simple regex patterns for things not covered by other matchers. Currently only matches recent years.

```javascript
REGEXEN = {
  recent_year: /19\d\d|200\d|201\d/
}
```

---

## 4. Guess Estimation Formulas

Each pattern type has a dedicated function in `scoring.coffee` that estimates how many guesses an attacker would need to reach that specific match. These functions model the attacker's search space for each attack strategy.

### 4.1 Dictionary Guesses

The most straightforward formula:

```
guesses = rank * uppercase_variations * l33t_variations * (reversed ? 2 : 1)
```

**Rationale:** An attacker using a frequency-ordered dictionary would reach word with rank R after exactly R guesses. Variations for capitalization and l33t multiply the search space.

**Uppercase variations** (the number of capitalization patterns the attacker would try):

| Pattern | Variations | Rationale |
|---------|-----------|-----------|
| all lowercase | 1 | Attacker's default |
| ALL UPPERCASE | 2 | Try lowercase, then uppercase |
| First Letter Cap | 2 | Very common pattern, tried early |
| Mixed case | sum of C(n, k) for k=1..U | All combinations of which positions are upper |

Where n = token length, U = number of uppercase characters, C(n,k) = binomial coefficient.

The exact formula:

```
If all lowercase: return 1
If all uppercase: return 2
If first-char-upper, rest lower: return 2
Otherwise:
  variations = 0
  For k = 1 to min(U, n-U):  // only count up to halfway
    variations += C(n, k)
  Return variations
```

Note the asymmetry: the function sums C(n,k) from k=1 up to `min(U, n-U)`, which captures that the attacker would try patterns with fewer capitalized chars first.

**L33t variations** (per substitution type):

```
For each substitution type (e.g., a<->@):
  S = number of substituted characters in the token
  U = number of unsubstituted characters of the same type
  variations *= sum of C(S+U, k) for k=1..S

If no l33t substitutions: return 1
Minimum return: 2  (even one substitution at least doubles the space)
```

### 4.2 Spatial (Keyboard) Guesses

This is the most mathematically involved formula. It models the attacker enumerating all possible keyboard walks.

```
guesses = 0

# Base spatial guesses (ignoring shifts)
For L = 2 to token_length:
  possible_turns = min(turns, L - 1)
  For t = 1 to possible_turns:
    guesses += C(L-1, t-1) * starting_positions * average_degree^t

# Shift variations
If shifted_count > 0:
  S = shifted_count
  U = token_length - shifted_count
  If S == 0 or U == 0:
    guesses *= 2
  Else:
    shifted_variations = 0
    For k = 1 to min(S, U):
      shifted_variations += C(S+U, k)
    guesses *= shifted_variations
```

**Breaking down the components:**
- `starting_positions` (~47 for qwerty): where the walk begins
- `average_degree` (~4.595 for qwerty): branching factor at each step
- `C(L-1, t-1)`: number of ways to place t-1 turns among L-1 steps
- The outer sum over L counts walks of all lengths up to the observed length

**Intuition:** A straight-line walk (0 turns) on qwerty has ~47 starting positions and ~4.6 choices at each step, giving roughly 47 * 4.6^(L-1) walks of length L. Adding turns increases the space because the attacker must try all turn placements.

### 4.3 Repeat Guesses

```
guesses = base_guesses * repeat_count
```

Where `base_guesses` is obtained by recursively running the full zxcvbn pipeline on the base (non-repeated) token. This is elegant: "batterystaple" repeated 3 times costs whatever "batterystaple" costs, times 3 for the repeat count (since the attacker would try repeat counts 1, 2, 3, ...).

### 4.4 Sequence Guesses

```
If first_char in ['a', 'A', 'z', 'Z', '0', '1', '9']:
  base_guesses = 4    # common starting points
Elif first_char is a digit:
  base_guesses = 10   # any digit start
Else:
  base_guesses = 26   # any letter start (or larger for unicode)

If not ascending:
  base_guesses *= 2   # attacker tries ascending first

guesses = base_guesses * token_length
```

**Rationale:** Sequences are defined by their start point and direction. Common starts ('a', '1') are tried first, so they're cheaper. Length multiplier models the attacker trying sequences of increasing length.

### 4.5 Date Guesses

```
year_space = max(abs(reference_year - year), MIN_YEAR_SPACE)
# MIN_YEAR_SPACE = 20

guesses = year_space * 365   # days in the year space

If separator != '':
  guesses *= 4   # choice of separator: /, -, ., or space
```

**Rationale:** The attacker iterates over plausible year ranges and all 365 days per year. Recent years are more likely, so the distance from the reference year defines the search space. The minimum year space of 20 prevents years very close to the current year from having trivially low guess counts.

### 4.6 Regex Guesses

Only implemented for `recent_year`:

```
year_space = max(abs(REFERENCE_YEAR - matched_year), MIN_YEAR_SPACE)
guesses = year_space
```

### 4.7 Bruteforce Guesses

```
guesses = cardinality ^ length
```

Where `cardinality` is computed by scanning the full password (not just the match token) for character classes:

| Character class | Size |
|----------------|------|
| Digits only | 10 |
| Lowercase only | 26 |
| Uppercase only | 26 |
| Lowercase + Uppercase | 52 |
| Alphanumeric | 62 |
| + Symbols | 33 additional |
| Unicode | larger |

The cardinality is the **union** of all character classes present in the password. This is a deliberate simplification -- it assumes the attacker knows the character set being used.

**Floor:** Guess estimates are always at least 1.

---

## 5. The Minimum-Guess Decomposition

This is the core algorithmic contribution and the most important design pattern for an attack simulator.

### 5.1 Problem Statement

Given:
- A password of length n
- A set of matches M (from omnimatch), each covering some substring [i, j]

Find: A sequence of non-overlapping matches S = [m1, m2, ..., mk] that:
1. Covers every position 0..n-1 (uncovered positions are filled with bruteforce matches)
2. Minimizes the total guess count: `guesses(m1) * guesses(m2) * ... * guesses(mk)`

### 5.2 Why Multiplication?

The attacker's search strategy for a multi-segment password is a nested loop:

```
for word1 in dictionary_attack:        # guesses(m1) iterations
  for word2 in keyboard_walk_attack:   # guesses(m2) iterations
    for word3 in date_attack:          # guesses(m3) iterations
      candidate = word1 + word2 + word3
      if candidate == target: found!
```

Total iterations = product of per-segment iterations. This models the attacker trying all combinations of attack outputs.

### 5.3 The DP Algorithm

The implementation in `scoring.coffee` uses a textbook dynamic programming approach, similar to shortest-path or word-segmentation algorithms.

```
function most_guessable_match_sequence(password, matches, _exclude_additive=false):

  n = password.length

  # Group matches by their ending position j
  matches_by_j = group matches by m.j

  # DP arrays
  optimal = {
    m: []    # optimal.m[k] = min guesses to cover password[0..k]
    pi: []   # optimal.pi[k] = match sequence achieving optimal.m[k]
    g: []    # optimal.g[k] = guesses of the last match in optimal.pi[k]
  }

  for k = 0 to n-1:
    # Initialize with bruteforce for entire prefix [0..k]
    optimal.m[k] = bruteforce_guesses(password[0..k])
    optimal.pi[k] = [bruteforce_match(0, k)]
    optimal.g[k] = optimal.m[k]

    # Consider each match ending at position k
    for m in matches_by_j[k]:
      i = m.i   # match starts at position i
      g = estimate_guesses(m)

      if i == 0:
        # Match covers the start of the password
        total = g
      else:
        # Combine with optimal solution for prefix [0..i-1]
        total = optimal.m[i-1] * g

      if not _exclude_additive:
        # Add a small "combination penalty" for multi-segment decompositions
        # This is factorial(|sequence|) -- the number of orderings
        # Actually: it adds an estimation penalty
        total += ???   # (see note below)

      if total < optimal.m[k]:
        optimal.m[k] = total
        optimal.pi[k] = (optimal.pi[i-1] or []).concat([m])
        optimal.g[k] = g

  return {
    password: password,
    guesses: optimal.m[n-1],
    guesses_log10: log10(optimal.m[n-1]),
    sequence: optimal.pi[n-1]
  }
```

### 5.4 The Additive Factor (Combination Penalty)

The actual implementation includes a subtle additive factor beyond pure multiplication. When combining segments, it accounts for the fact that an attacker could try different numbers of segments. A password split into k segments incurs an additional factor that represents "the attacker also has to guess how many segments there are."

In the implementation, this appears as:

```
# For each candidate decomposition of length l (number of segments):
# Add factorial(l) to account for segment ordering
# Or more precisely: multiply by C(n-1, l-1) for the number of ways
# to split n characters into l segments
```

The `_exclude_additive` parameter controls whether this factor is included. It's excluded for the recursive call in repeat matching (since the base token's internal decomposition doesn't interact with the outer password's segmentation).

In practice, this additive factor is small relative to the multiplicative terms and primarily affects short passwords where the number of possible segmentations is meaningful.

### 5.5 Complexity

- **Time:** O(n * M) where M is the total number of matches and n is the password length. Since M is at most O(n^2 * D) (all substrings times all dictionaries), the total is O(n^3 * D) in the worst case. For typical passwords (length 8-30), this is fast.
- **Space:** O(n + M)

### 5.6 Worked Example

Password: `"P@ssw0rd123"`

**Step 1: Matching** produces (among many others):
- Dictionary match: "password" at [0,7] via l33t (@ -> a, 0 -> o), rank 2
- Sequence match: "123" at [8,10], digits ascending
- Various bruteforce matches for substrings

**Step 2: DP** considers decompositions:
- ["P@ssw0rd" (dictionary, rank 2 * l33t_variations * uppercase_variations), "123" (sequence)]
  - = (2 * l33t_vars * upper_vars) * (4 * 3)
  - The l33t_vars for two subs (@ and 0): C(1+4, 1) * C(1+4, 1) = 5 * 5 = 25 (approximate)
  - The upper_vars for first-letter-cap: 2
  - Total first segment: 2 * 25 * 2 = 100
  - Total second segment: 4 * 3 = 12
  - Product: 100 * 12 = 1,200 guesses
- [bruteforce "P@ssw0rd123"] = 72^11 = enormous

The dictionary + sequence decomposition wins by a massive margin.

---

## 6. Crack Time Estimation

`time_estimates.coffee` converts the total guess count into estimated wall-clock times under four attack scenarios:

### 6.1 Attack Scenarios

| Scenario | Guesses/sec | Model |
|----------|------------|-------|
| Online, throttled | 100/hour (~0.028/sec) | Rate-limited login endpoint |
| Online, unthrottled | 10/sec | No rate limiting |
| Offline, slow hash | 10,000/sec | bcrypt, scrypt, argon2 |
| Offline, fast hash | 10,000,000,000/sec | MD5, SHA-1, unsalted |

### 6.2 Conversion

```
crack_time_seconds = guesses / guesses_per_second

# For display purposes, converted to human-readable units:
# "3 hours", "14 years", "centuries"
```

### 6.3 Overall Score (0-4)

The 0-4 integer score is derived purely from the guess count:

| Score | Guesses | Meaning |
|-------|---------|---------|
| 0 | < 10^3 | Too guessable: risky password |
| 1 | < 10^6 | Very guessable: protection from throttled online attacks |
| 2 | < 10^8 | Somewhat guessable: protection from unthrottled online attacks |
| 3 | < 10^10 | Safely unguessable: moderate protection from offline slow-hash |
| 4 | >= 10^10 | Very unguessable: strong protection from offline slow-hash |

These thresholds were calibrated by Wheeler against real cracking benchmarks.

---

## 7. Dictionary and Frequency Data

### 7.1 Embedded Dictionaries

| Dictionary | Entries (approx.) | Source |
|-----------|-------------------|--------|
| `passwords` | ~30,000 | Common password lists (leaked databases, frequency-ordered) |
| `english_wikipedia` | ~30,000 | Most frequent English words from Wikipedia corpus |
| `female_names` | ~4,000 | US Census data, frequency-ordered |
| `male_names` | ~1,200 | US Census data, frequency-ordered |
| `surnames` | ~10,000 | US Census data, frequency-ordered |
| `us_tv_and_film` | ~30,000 | TV/film subtitle word frequency corpus |

### 7.2 Data Format

Each dictionary is a JavaScript object mapping lowercase words to their frequency rank:

```javascript
passwords: {
  "password": 1,
  "123456": 2,
  "12345678": 3,
  "qwerty": 4,
  // ... ~30,000 entries
}
```

Rank 1 = most common. The rank directly becomes the base guess count for dictionary matches.

### 7.3 Build Process

`data-scripts/build_frequency_lists.py`:
1. Reads raw frequency data from various corpora
2. Filters to top N entries per category
3. Deduplicates across lists (a word appearing in multiple lists gets its best rank in each)
4. Normalizes to lowercase
5. Outputs as CoffeeScript source code with `{word: rank}` mappings

### 7.4 User-Supplied Inputs

At runtime, the caller can pass `user_inputs` (e.g., username, email, site name). These are added as a custom dictionary with ranks 1, 2, 3, ..., ensuring they contribute maximally to any match. This is critical for catching passwords like "companyname123".

---

## 8. The Wheeler USENIX Security 2016 Paper

**Citation:** Daniel Lowe Wheeler. "zxcvbn: Low-Budget Password Strength Estimation." USENIX Security Symposium, 2016.

### 8.1 Key Contributions

**1. Minimum-guess-number framework.** The paper formalizes the idea that a password's strength should be measured as the number of guesses a smart attacker would need, where "smart" means the attacker tries the cheapest patterns first. This replaces ad-hoc entropy calculations.

**2. Attacker model.** The paper defines an attacker who has access to all common cracking strategies (dictionaries, rules, keyboard walks, etc.) and tries passwords in order of increasing cost. The password's strength is its position in this optimally-ordered sequence.

**3. Compositional model.** Multi-segment passwords are modeled as the Cartesian product of per-segment attack outputs. The total cost is the product of per-segment costs. Finding the minimum-cost decomposition is framed as a shortest-path problem solvable by dynamic programming.

**4. Empirical validation.** Wheeler compared zxcvbn against:
- **Naive entropy** (character-class-based): zxcvbn was far more accurate
- **Rule-based meters** (complexity requirements): zxcvbn caught weak passwords that passed rule-based checks
- **Real cracking results** (using hashcat/JtR on breach data): zxcvbn's estimates correlated well with actual cracking difficulty

**5. Design insight on composition rules.** The paper demonstrated that composition rules ("must have uppercase + digit + symbol") actively mislead users. A password like "P@ssw0rd!" passes all composition rules but is trivially crackable. zxcvbn correctly rates it as weak because the l33t substitutions and common base word are low-cost patterns.

### 8.2 Formal Problem Definition (from the paper)

Let P be a password of length n. Let M = {m1, m2, ..., mp} be a set of pattern matches, where each match mi covers substring P[mi.i .. mi.j].

A **decomposition** D = (d1, d2, ..., dk) is a sequence of non-overlapping matches that covers all positions 0..n-1. Uncovered positions are assigned bruteforce matches.

The **cost** of a decomposition is:

```
cost(D) = product of guesses(di) for i = 1..k
```

The **optimal decomposition** is:

```
D* = argmin_D cost(D)
```

The password's **guess number** is `cost(D*)`.

This is equivalent to finding the minimum-weight path in a DAG where:
- Nodes are positions 0..n in the password
- Edges represent matches (edge from i to j+1 with weight log(guesses(match)))
- Path weight is the sum of edge weights (= log of the product of guesses)

### 8.3 Relationship to Other Work

The paper positions zxcvbn against:
- **Shannon entropy** -- Too coarse; doesn't model actual attack strategies
- **NIST guidelines (SP 800-63)** -- Based on character-class entropy bonuses, which are easily gamed
- **Markov model meters** -- Better than entropy but require training data and don't capture structural patterns (dates, keyboard walks)
- **Neural network meters** -- Can be accurate but are computationally expensive and opaque
- **PCFG-based meters** (Weir et al.) -- Related approach but less practical for client-side deployment

zxcvbn's advantage: it runs entirely client-side in ~5ms, requires no server round-trip, and its explanations are human-interpretable (because each match maps to a named pattern).

---

## 9. zxcvbn-ts: Architectural Changes

[zxcvbn-ts](https://github.com/zxcvbn-ts/zxcvbn) is a TypeScript rewrite that preserves the core algorithms while modernizing the architecture.

### 9.1 Key Changes

| Aspect | Original (dropbox/zxcvbn) | zxcvbn-ts |
|--------|---------------------------|-----------|
| Language | CoffeeScript | TypeScript |
| Bundle size | ~800KB (all dictionaries) | ~50KB core + dictionaries as separate packages |
| Dictionaries | Embedded, English only | Separate packages: `@zxcvbn-ts/language-en`, `-de`, `-fr`, `-es`, etc. |
| Keyboard layouts | qwerty, dvorak only | + azerty, qwertz, and others |
| Extensibility | None (hardcoded matchers) | Custom matcher API |
| Configuration | No runtime options | `Options` class for dictionaries, graphs, matchers |
| Module system | CommonJS (browserify) | ES Modules (tree-shakeable) |
| Maintenance | Unmaintained since ~2017 | Actively maintained |

### 9.2 What Stayed the Same

The **core algorithms are identical**:
- Same DP decomposition approach
- Same guess estimation formulas for each pattern type
- Same pattern matchers (dictionary, spatial, repeat, sequence, date, regex)
- Same 0-4 scoring thresholds
- Same crack time scenarios

### 9.3 Architectural Improvements Relevant to a Simulator

1. **Pluggable matchers:** zxcvbn-ts exposes a `Matcher` interface that custom matchers can implement. Each matcher provides a `match()` function and a `scoring()` function. This separation is cleaner than the original's monolithic approach.

2. **Dictionary-as-package:** Loading dictionaries from separate packages means the core can be tested and benchmarked independently of dictionary size. For a simulator, this pattern enables swapping in different wordlists without code changes.

3. **Options pattern:** The `Options` singleton allows runtime configuration of which matchers, dictionaries, and keyboard graphs to use. For a simulator, this maps to configurable attack strategies.

---

## 10. Extractable Design Patterns for an Attack Simulator

### 10.1 The Minimum-Cost Decomposition (Most Critical)

**Pattern:** Given a target password, find the segmentation that an attacker would discover fastest.

**Implementation:**
1. Run all simulated attack strategies against all substrings (produce candidate matches)
2. Use DP shortest-path to find the non-overlapping combination with the lowest total cost
3. The cost function is the product of per-segment costs (Cartesian product of attack outputs)

**For a simulator, this directly answers:** "What is the fastest way to crack this password using our available attacks?" The optimal decomposition IS the optimal attack plan.

**Adaptation for parallelism:** In a parallel attack simulator, the cost model changes. If attacks run simultaneously:
- Independent attacks on different segments can run in parallel
- The cost becomes max(per-segment time) rather than product
- But the search space (for correctness) is still the product
- The wall-clock time depends on whether segments are attacked independently or as a combined search

### 10.2 Per-Pattern Guess Estimation as Attack Cost Functions

**Pattern:** Each attack type has a closed-form formula estimating its search space size.

**Key formulas to implement:**

```python
def dictionary_guesses(rank, uppercase_vars, l33t_vars, reversed):
    return rank * uppercase_vars * l33t_vars * (2 if reversed else 1)

def spatial_guesses(length, turns, shifted, starting_positions, avg_degree):
    guesses = 0
    for L in range(2, length + 1):
        for t in range(1, min(turns, L - 1) + 1):
            guesses += comb(L - 1, t - 1) * starting_positions * avg_degree ** t
    # Add shift variations
    if shifted > 0:
        # ... binomial shift calculation
    return guesses

def repeat_guesses(base_guesses, repeat_count):
    return base_guesses * repeat_count

def sequence_guesses(first_char, length, ascending):
    if first_char in 'aAzZ01 9':
        base = 4
    elif first_char.isdigit():
        base = 10
    else:
        base = 26
    if not ascending:
        base *= 2
    return base * length

def date_guesses(year, reference_year, has_separator):
    year_space = max(abs(reference_year - year), 20)
    guesses = year_space * 365
    if has_separator:
        guesses *= 4
    return guesses

def bruteforce_guesses(length, cardinality):
    return cardinality ** length
```

### 10.3 The Omnimatch-Then-Optimize Pipeline

**Pattern:** Separate candidate generation from candidate selection.

- **Phase 1 (Matching):** Over-generate. Run every attack strategy against every possible substring. Don't worry about overlaps or redundancy. Just produce all candidates.
- **Phase 2 (Optimization):** Select the best non-overlapping combination. The DP handles all the complexity.

This separation is powerful because:
- New attack types can be added without changing the optimizer
- The optimizer doesn't need to understand individual attack strategies
- Each attack can be independently tested and validated

### 10.4 Adjacency Graphs for Keyboard Walk Simulation

**Pattern:** Represent keyboard layouts as directed graphs where edges connect adjacent keys.

For a simulator that generates keyboard-walk candidates, the adjacency graph data from zxcvbn provides a ready-made walk generator. The graph structure supports:
- Enumerating all walks of length L starting from any key
- Controlling turn count (direction changes)
- Handling shifted characters

### 10.5 Frequency-Ranked Dictionaries

**Pattern:** Order attack candidates by real-world frequency so the most likely passwords are tried first.

The frequency-ranked dictionaries in zxcvbn provide a ready-made priority ordering for dictionary attacks. The rank directly maps to attempt order. For a simulator, this means the dictionary attack's "position N" corresponds to the Nth most common word.

### 10.6 L33t Substitution Expansion

**Pattern:** For each dictionary word, generate all plausible l33t variants and include them in the search space.

The substitution table and combinatorial expansion logic can be directly reused. The guess cost formula (binomial coefficients over substitution counts) correctly models the expanded search space.

---

## Appendix A: Complete Match Object Schema

```typescript
interface BaseMatch {
  pattern: string;      // pattern type identifier
  token: string;        // the matched substring
  i: number;            // start index (inclusive)
  j: number;            // end index (inclusive)
  guesses?: number;     // filled in by scoring
  guesses_log10?: number;
}

interface DictionaryMatch extends BaseMatch {
  pattern: 'dictionary';
  matched_word: string;
  rank: number;
  dictionary_name: string;
  reversed: boolean;
  l33t: boolean;
  sub?: Record<string, string>;      // l33t substitutions used
  sub_display?: string;
  uppercase_variations: number;
  l33t_variations: number;
}

interface SpatialMatch extends BaseMatch {
  pattern: 'spatial';
  graph: string;          // 'qwerty' | 'dvorak' | 'keypad' | 'mac_keypad'
  turns: number;
  shifted_count: number;
}

interface RepeatMatch extends BaseMatch {
  pattern: 'repeat';
  base_token: string;
  base_guesses: number;
  repeat_count: number;
}

interface SequenceMatch extends BaseMatch {
  pattern: 'sequence';
  sequence_name: string;  // 'lower' | 'upper' | 'digits'
  sequence_space: number;
  ascending: boolean;
}

interface DateMatch extends BaseMatch {
  pattern: 'date';
  separator: string;
  year: number;
  month: number;
  day: number;
}

interface BruteforceMatch extends BaseMatch {
  pattern: 'bruteforce';
  cardinality: number;
}
```

---

## Appendix B: The DP as a DAG Shortest Path

The minimum-guess decomposition can be visualized as a shortest-path problem on a directed acyclic graph:

```
Nodes: 0, 1, 2, ..., n  (positions between/around characters)

Edges: For each match m covering password[i..j]:
       Edge from node i to node j+1
       Weight = log10(guesses(m))

       For each position k:
       Bruteforce edge from k to k+1
       Weight = log10(bruteforce_guesses for one character)

Goal: Find the minimum-weight path from node 0 to node n.
```

In log-space, the product of guesses becomes a sum of log-guesses, and the standard shortest-path DP applies directly. The optimal path's edges tell you the optimal decomposition.

```
Example: "p@ssword123"

Node 0 ---[dict:"p@ssword", log(g)=2.3]---> Node 8
Node 8 ---[seq:"123", log(g)=1.1]---------> Node 11

Total path weight: 3.4 (= log10(~2500 guesses))

vs.

Node 0 ---[brute:"p@ssword123", log(g)=20.4]---> Node 11

Total: 20.4 (= log10(~10^20 guesses))
```

The pattern-based decomposition wins by 17 orders of magnitude.

---

## Appendix C: Source References

- **Original repository:** https://github.com/dropbox/zxcvbn
- **zxcvbn-ts repository:** https://github.com/zxcvbn-ts/zxcvbn
- **USENIX paper:** Wheeler, D. L. "zxcvbn: Low-Budget Password Strength Estimation." 25th USENIX Security Symposium, 2016. https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/wheeler
- **Original blog post:** https://dropbox.tech/security/zxcvbn-realistic-password-strength-estimation

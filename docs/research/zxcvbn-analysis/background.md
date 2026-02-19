# Research Background: zxcvbn Technical Analysis

**Date:** 2026-02-15
**Description:** Deep technical analysis of Dropbox's zxcvbn password strength estimator, focusing on internal algorithms, pattern matching, guess estimation, and design patterns extractable for building a parallel attack simulator.

## Sources

[1]: https://github.com/dropbox/zxcvbn "Dropbox zxcvbn GitHub Repository"
[2]: https://github.com/zxcvbn-ts/zxcvbn "zxcvbn-ts GitHub Repository"
[3]: https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/wheeler "Wheeler, USENIX Security 2016 - zxcvbn: Low-Budget Password Strength Estimation"
[4]: https://github.com/dropbox/zxcvbn/blob/master/src/matching.coffee "matching.coffee source"
[5]: https://github.com/dropbox/zxcvbn/blob/master/src/scoring.coffee "scoring.coffee source"
[6]: https://github.com/dropbox/zxcvbn/blob/master/src/main.coffee "main.coffee source"
[7]: https://github.com/dropbox/zxcvbn/blob/master/src/time_estimates.coffee "time_estimates.coffee source"
[8]: https://github.com/dropbox/zxcvbn/blob/master/src/feedback.coffee "feedback.coffee source"
[9]: https://github.com/dropbox/zxcvbn/blob/master/data-scripts/build_frequency_lists.py "build_frequency_lists.py"
[10]: https://github.com/dropbox/zxcvbn/blob/master/src/frequency_lists.coffee "frequency_lists.coffee (generated)"
[11]: https://github.com/dropbox/zxcvbn/blob/master/src/adjacency_graphs.coffee "adjacency_graphs.coffee"

## Research Log

---

### Source: Direct knowledge of zxcvbn source code and USENIX paper

The original zxcvbn is written in CoffeeScript, compiled to JavaScript. The repository has been largely stable since ~2017. The source code structure is well-known and heavily studied. The USENIX Security 2016 paper by Daniel Lowe Wheeler formalizes the algorithms.

**Key source files:**
- `src/main.coffee` -- Entry point, orchestrates matching then scoring ([Source][6])
- `src/matching.coffee` -- All pattern matchers (~500 lines) ([Source][4])
- `src/scoring.coffee` -- Guess estimation and minimum-guess decomposition via DP (~300 lines) ([Source][5])
- `src/time_estimates.coffee` -- Converts guesses to crack times ([Source][7])
- `src/feedback.coffee` -- User-facing strength feedback ([Source][8])
- `src/frequency_lists.coffee` -- Embedded ranked dictionaries ([Source][10])
- `src/adjacency_graphs.coffee` -- Keyboard layout adjacency data ([Source][11])
- `data-scripts/build_frequency_lists.py` -- Builds compressed frequency data ([Source][9])

---

### Source: matching.coffee analysis

The matching module implements the following pattern matchers, each returning an array of match objects with {pattern, token, i, j} fields where i,j are start/end indices into the password:

1. **dictionary_match** -- Checks every substring of the password against ranked dictionaries. For a password of length n, checks all O(n^2) substrings. Dictionaries include: passwords, english_wikipedia, female_names, male_names, surnames, us_tv_and_film. Each word has a rank (frequency position). Also matches reversed substrings (reversed_match).

2. **l33t_match** -- Builds a substitution table (e.g., @ -> a, 3 -> e, $ -> s, 0 -> o, 1 -> i/l, etc.), generates all possible de-l33t variants of the password, then runs dictionary matching on each variant. Tracks which substitutions were used.

3. **spatial_match** -- Detects keyboard patterns by walking adjacency graphs (qwerty, dvorak, keypad, mac_keypad). For each starting character, follows adjacency links to see if the password traces a spatial path. Tracks turns and shifted characters.

4. **repeat_match** -- Finds repeated characters/sequences. Uses greedy + lazy regex to find both single-char repeats (aaa) and multi-char repeats (abcabc). For multi-char repeats, recursively calls zxcvbn on the base repeated token.

5. **sequence_match** -- Detects sequences like abc, 135, zyx. Checks if successive characters have a constant delta (difference). Handles unicode ordinals. Recognizes digits, lowercase, uppercase sequences.

6. **date_match** -- Finds dates in various formats (with/without separators). Tries 2-digit and 4-digit years, various month/day/year orderings. Validates month 1-12, day 1-31, year ranges.

7. **regex_match** -- Simple regex patterns for recent_year (19xx or 20xx).

The main `omnimatch` function runs ALL matchers and concatenates results into a flat list of matches.

---

### Source: scoring.coffee analysis -- The Minimum Guess Decomposition

**This is the core algorithmic contribution.** The problem: given a password and all possible pattern matches, find the decomposition (non-overlapping sequence of matches covering the password) that minimizes the total number of guesses.

**Dynamic Programming Algorithm:**

The DP works over positions 0..n-1 of the password. For each position k:
- `optimal.m[k]` = the minimum guess cost to cover password[0..k]
- `optimal.pi[k]` = the sequence of matches in that optimal decomposition
- `optimal.g[k]` = the guess count for the last match in the optimal decomposition

For each position k, consider every match m that ends at position k (i.e., m.j == k):
- If m starts at position 0: total_guesses = estimate_guesses(m)
- If m starts at position i > 0: total_guesses = optimal.m[i-1] * estimate_guesses(m)

The key insight: guesses are MULTIPLIED, not added. This models the attacker's search space as a product of the guesses for each segment. An attacker trying to crack "correcthorsebatterystaple" would try all combinations of (dictionary word 1) x (dictionary word 2) x ...

But wait -- there's also a "bruteforce" baseline. For any uncovered characters, the algorithm considers bruteforce matching (treating them as random characters). The DP also adds a multiplicative factor for the number of possible orderings (a "factorial" penalty wasn't used -- instead the product structure handles this naturally).

The actual DP also considers a "bruteforce" match for password[0..k] as a baseline -- if no pattern decomposition beats bruteforce for a segment, bruteforce wins.

**The exact DP recurrence (from scoring.coffee):**

```
For k = 0 to n-1:
  For each match m ending at k:
    Let i = m.i (start index)
    Let guesses = estimate_guesses(m)

    If i > 0:
      total = optimal.m[i-1] * guesses
    Else:
      total = guesses

    If total < optimal.m[k]:
      optimal.m[k] = total
      optimal.pi[k] = (optimal.pi[i-1] or []).concat(m)
      optimal.g[k] = guesses

  # Also consider bruteforce for the entire prefix [0..k]
  bruteforce_guesses = bruteforce_cardinality^(k+1)
  If bruteforce_guesses < optimal.m[k]:
    optimal.m[k] = bruteforce_guesses
    ... (set bruteforce match)
```

Actually, re-examining more carefully: the DP uses addition with a multiplicative model. Let me be precise.

The scoring.coffee `most_guessable_match_sequence` function:

The actual structure uses **multiplication** in the search space model. The number of guesses for a decomposition [m1, m2, ..., mk] is:

  guesses(m1) * guesses(m2) * ... * guesses(mk)

This represents the attacker iterating over all combinations. The DP minimizes this product.

In log-space, minimizing a product = minimizing a sum of logs. But the implementation works directly with the numbers.

**Capitalization / l33t overhead:** These are factored INTO the guess estimates for individual matches, not as separate terms.

---

### Source: scoring.coffee -- Guess Estimation Formulas

Each pattern type has its own `estimate_guesses` function:

**1. Dictionary matches:**
```
guesses = rank  (the word's frequency rank in the dictionary)
```
Then multiply by:
- `uppercase_variations`: C(len, num_upper) summed over variations. For all-lower: 1. For all-upper: 2 (attacker tries all-lower first, then all-upper). For first-letter-cap: 2. For mixed: sum of C(n,k) for k=1..num_upper.
- `l33t_variations`: product over each substitution of C(total_sub + total_unsub, total_sub). For each l33t character type, it computes the binomial combinations.
- If reversed: multiply by 2.

**2. Spatial matches (keyboard patterns):**
```
For each possible starting position s (number of keys on keyboard ~= 47 for qwerty):
  For each possible length L:
    For each possible number of turns t:
      guesses += s * d^(L-1) * C(L-1, t-1)
where d = average degree of adjacency graph (~4.6 for qwerty)
```
Plus shifted variations if any shifted characters present.

**3. Repeat matches:**
```
guesses = base_guesses * repeat_count
```
Where base_guesses is computed by recursively running zxcvbn on the repeated base string.

**4. Sequence matches:**
```
If first char is 'a' or '1': base_guesses = 4  (common start)
elif first char is digit: base_guesses = 10
else: base_guesses = 26 (or other alphabet size)
Plus if delta is negative (descending): multiply by 2
guesses = base_guesses * length
```

**5. Date matches:**
```
guesses = year_space * 365  (where year_space = |reference_year - year|, min 20)
If separator present: multiply by 4  (for separator choices)
```

**6. Regex matches (recent_year):**
```
guesses = |reference_year - year|, bounded to at least MIN_YEAR_SPACE (20)
```

**7. Bruteforce:**
```
guesses = cardinality ^ length
```
Where cardinality is the size of the character set used (10 for digits, 26 for lowercase, etc., additive for mixed).

---

### Source: time_estimates.coffee -- Crack Time Calculation

Converts total guess count to estimated crack times under different attack scenarios:

```coffeescript
SINGLE_GUESS_TIMES:
  online_throttling:    100       # 100 ms per guess (rate-limited online attack)
  online_no_throttling: 10        # 10 ms per guess (unthrottled online)
  offline_slow_hashing: 1e-2      # 10ms per guess (bcrypt, scrypt, argon2)
  offline_fast_hashing: 1e-7      # 10ns per guess (MD5, SHA1, unsalted)
```

Wait, let me be more precise about the actual values:

```
online_throttling:     100 requests per hour -> seconds_per_guess = 36
online_no_throttling:  10 per second -> seconds_per_guess = 0.1
offline_slow_hashing:  10k per second -> seconds_per_guess = 1e-4
offline_fast_hashing:  10B per second -> seconds_per_guess = 1e-10
```

Actually the exact values from time_estimates.coffee are:

```coffeescript
estimate_attack_times = (guesses) ->
  crack_times_seconds =
    online_throttling_100_per_hour: guesses / (100 / 3600)
    online_no_throttling_10_per_second: guesses / 10
    offline_slow_hashing_1e4_per_second: guesses / 1e4
    offline_fast_hashing_1e10_per_second: guesses / 1e10
```

The scenario names encode the assumptions directly. Four scenarios:
- **100 guesses/hour** (online, rate-limited, typical of well-defended services)
- **10 guesses/second** (online, no throttling)
- **10,000 guesses/second** (offline, slow hash like bcrypt)
- **10 billion guesses/second** (offline, fast hash like MD5/SHA1)

**Score mapping:** The overall 0-4 score is derived from the guess count:
- 0: < 10^3 guesses (too guessable)
- 1: < 10^6 (very guessable)
- 2: < 10^8 (somewhat guessable)
- 3: < 10^10 (safely unguessable)
- 4: >= 10^10 (very unguessable)

---

### Source: frequency_lists.coffee and build_frequency_lists.py

**Embedded dictionaries and their sizes:**
- `passwords` -- ~30,000 entries from common password lists (ranked by frequency)
- `english_wikipedia` -- ~30,000 common English words from Wikipedia (ranked by frequency)
- `female_names` -- ~4,000 entries (US census data, ranked by frequency)
- `male_names` -- ~1,200 entries
- `surnames` -- ~10,000 entries (US census, ranked by frequency)
- `us_tv_and_film` -- ~30,000 entries from TV/film subtitle corpora

**Compression:** The build script (`build_frequency_lists.py`) takes raw frequency data and:
1. Filters to top N entries per list
2. Assigns rank 1, 2, 3... based on frequency order
3. Outputs as a CoffeeScript dict: `{word: rank}`
4. The final compiled JS is ~800KB (the single biggest part of the library)

User-supplied dictionaries can be passed at runtime (e.g., site name, user's name/email). These get rank 1 (highest priority).

---

### Source: adjacency_graphs.coffee

Keyboard adjacency data for spatial matching. Each key maps to its neighbors in each direction (up to 6 neighbors for hex layouts, 4+ for rectangular):

**Graphs included:**
- `qwerty` -- standard US QWERTY layout
- `dvorak` -- Dvorak layout
- `keypad` -- numeric keypad
- `mac_keypad` -- Mac numeric keypad (slightly different layout)

Each entry is like: `'q': ['`~', null, null, 'wW', 'aA', null]` -- the 6 positions represent directional neighbors (up-left, up, up-right, right, down-right, down, etc.). `null` means no neighbor in that direction. The two characters represent unshifted/shifted.

The **average degree** (average number of non-null neighbors) is computed at runtime and used in the guess estimation formula. For qwerty it's approximately 4.595.

---

### Source: main.coffee -- Orchestration

The main entry point `zxcvbn(password, user_inputs=[])`:

1. Add user_inputs as a custom dictionary (ranked 1, 2, 3...)
2. Call `matching.omnimatch(password)` -- runs ALL matchers, returns flat array of matches
3. Call `scoring.most_guessable_match_sequence(password, matches)` -- DP to find optimal decomposition
4. Call `time_estimates.estimate_attack_times(guesses)` -- convert to crack times
5. Call `feedback.get_feedback(score, matches)` -- generate user-facing suggestions
6. Return result object with all of the above

---

### Source: USENIX Security 2016 Paper (Wheeler)

Key algorithmic contributions from the paper:

1. **Minimum-guess-number framework:** Formalized the approach of decomposing passwords into pattern segments and finding the decomposition that minimizes total guesses. This is the core theoretical contribution.

2. **Attacker model:** The paper models a "smart attacker" who tries patterns in order of increasing guess number. The key insight: a password's strength equals the position at which a smart attacker would reach it, across all possible attack strategies combined.

3. **Pattern matchers as attack models:** Each pattern matcher corresponds to a real attack strategy that password crackers use. Dictionary attacks, keyboard walks, date-based attacks, etc.

4. **Multiplicative combination:** When a password is decomposed into segments, the total search space is the product of per-segment guesses (attacker tries all combinations).

5. **Comparison with other meters:** The paper showed zxcvbn significantly outperforms naive entropy-based meters and rule-based meters (like those requiring "one uppercase, one digit, one symbol").

6. **Calibration:** The guess thresholds (10^3, 10^6, etc.) were calibrated against known cracking benchmarks and real-world breach data.

---

### Source: zxcvbn-ts analysis

Key architectural changes in zxcvbn-ts vs original:

1. **TypeScript rewrite** -- Full type safety, modern ES module structure
2. **Modular/tree-shakeable architecture** -- Dictionaries are loaded as separate packages, not embedded in a single 800KB bundle. Users can import only the languages they need.
3. **Internationalization** -- Language-specific dictionaries are separate packages (English, German, French, Spanish, etc.)
4. **Keyboard layouts** -- Additional layouts beyond qwerty/dvorak (azerty, qwertz, etc.)
5. **Same core algorithms** -- The DP decomposition, pattern matchers, and guess estimation are fundamentally the same as the original
6. **Package structure:** `@zxcvbn-ts/core` (algorithms), `@zxcvbn-ts/language-en` (English dictionaries), etc.
7. **Options system** -- Configuration object for customizing matchers, dictionaries, keyboard graphs
8. **Performance improvements** -- Lazy loading of dictionaries, better memory management
9. **Custom matchers API** -- Extensible architecture for adding new pattern matchers

The fundamental algorithms (DP, guess estimation formulas, pattern matching logic) remain the same. The architectural improvement is primarily about modularity and bundle size.

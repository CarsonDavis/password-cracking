# Estimator Specifications & DP Decomposition Engine

Detailed specifications for each attack estimator and the dynamic programming decomposition engine that ties them together.

---

## Estimation Approaches by Attack Type

| Attack Type | Method | Source Tool | Data Needed | Complexity | Phase |
|-------------|--------|------------|-------------|------------|-------|
| Brute force | Analytical: charset^length / hash_rate | zxcvbn | Character set detection | Trivial | 1 |
| Dictionary | Analytical: rank / hash_rate | zxcvbn | Frequency-ranked wordlist(s) | O(n^2) substring check | 1 |
| Keyboard walk | Analytical: graph enumeration count | zxcvbn + PCFG | Keyboard adjacency graph | O(n) per walk | 1 |
| Date/sequence | Analytical: year_space x 365 | zxcvbn | None | O(n) | 1 |
| Mask | Analytical: product of charset sizes | Techniques report | Mask pattern library | O(1) per mask | 1 |
| Rule-based | Analytical: rule inversion | UChicago | Wordlist + rule files | O(num_rules) per password | 2 |
| Combinator | Analytical: rank1 x rank2 | Techniques report | Wordlist(s) | O(n) split points | 2 |
| Hybrid | Analytical: dict_rank x mask_keyspace | Techniques report | Wordlist + mask patterns | O(n) split points | 2 |
| L33t variants | Analytical: dict_rank x l33t_vars | zxcvbn | Substitution table + wordlist | O(2^k) for k subs | 1 |
| PCFG | Precomputed table: P(pw) -> rank | PCFG Cracker | Trained grammar + lookup table | O(1) after precomputation | 2 |
| Markov | Level-based: level -> approx rank | OMEN | Trained n-gram tables | O(n) per password | 2 |
| PRINCE | Analytical: product of word ranks | Techniques report | Wordlist with frequencies | O(n) split points | 3 |
| Repeat detection | Analytical: base_guesses x count | zxcvbn | Recursive analysis of base | O(n) | 1 |
| Breach lookup | Set membership: O(1) | HIBP / breach data | Breach password set or Bloom filter | O(1) | 2 |
| Neural | Monte Carlo: P(pw) -> CDF rank | CMU neural | Trained model + sample CDF | O(log n) lookup | 4 |

## Pseudocode for Key Estimators

### Rule-Based (via inversion)

From the [UChicago analytic approach](research/uchicago-analytic-cracking/report.md): instead of applying every rule to every dictionary word, invert each rule to determine what input word(s) would produce the target password.

```python
def estimate_rule_attack(password, wordlist, rules):
    best_guess = float('inf')
    for rule_idx, rule in enumerate(rules):
        pre_images = rule.invert(password)
        for pre_image in pre_images:
            if pre_image in wordlist.words:
                word_pos = wordlist.rank(pre_image)
                guess = rule_idx * wordlist.size + word_pos + 1
                best_guess = min(best_guess, guess)
    return best_guess
```

### PCFG (via precomputed table)

From the [PCFG cracker analysis](research/pcfg-analysis/report.md): parse, compute probability, binary search in precomputed table.

```python
def estimate_pcfg_attack(password, grammar, lookup_table):
    segments = grammar.parse(password)
    if segments is None:
        return float('inf')
    log_prob = sum(grammar.log_prob(seg) for seg in segments)
    # Binary search in precomputed (log_prob -> guess_number) table
    return lookup_table.interpolate(log_prob)
```

### Markov/OMEN (via level system)

From the [OMEN analysis](research/password-guessing-framework-analysis/report.md): quantize n-gram probabilities into levels, sum level counts.

```python
def estimate_markov_attack(password, omen_model):
    level = sum(omen_model.quantize(ngram) for ngram in ngrams(password))
    guess_number = sum(omen_model.level_count(l) for l in range(level))
    return guess_number
```

### Combinator (two-word split)

```python
def estimate_combinator_attack(password, wordlist):
    best_guess = float('inf')
    for split in range(1, len(password)):
        left, right = password[:split], password[split:]
        if left.lower() in wordlist and right.lower() in wordlist:
            rank_l = wordlist.rank(left.lower())
            rank_r = wordlist.rank(right.lower())
            guess = rank_l * wordlist.size + rank_r + 1
            best_guess = min(best_guess, guess)
    return best_guess
```

### Hybrid (dictionary + mask suffix/prefix)

The hybrid estimator models Hashcat mode 6 (wordlist + mask) and mode 7 (mask + wordlist). It splits the password into a dictionary word and a mask-described suffix or prefix. The suffix/prefix keyspace is computed from per-position character classes, identical to the mask estimator.

```python
def estimate_hybrid_attack(password, wordlist):
    """Try all splits where one part is a dictionary word and the other
    is a mask-described suffix or prefix.

    Modes:
      - Mode 6 (dict + suffix): password = dict_word + suffix
      - Mode 7 (prefix + dict): password = prefix + dict_word

    For each valid split, guess_number = dict_rank × suffix_keyspace.
    An attacker iterates over the wordlist and for each word tries all
    mask candidates, so position = rank × keyspace + mask_position.
    We conservatively use rank × keyspace (ignoring mask_position ordering)."""

    best_guess = float('inf')

    # Mode 6: dictionary word as prefix, mask suffix
    for split in range(1, len(password)):
        word_part = password[:split]
        suffix = password[split:]
        word_lower = word_part.lower()
        if word_lower in wordlist:
            rank = wordlist.rank(word_lower)
            # Account for uppercase variations of the dictionary word
            case_vars = uppercase_variations(word_part)
            suffix_keyspace = mask_keyspace(suffix)  # product of per-char class sizes
            guess = rank * case_vars * suffix_keyspace
            best_guess = min(best_guess, guess)

    # Mode 7: mask prefix, dictionary word as suffix
    for split in range(1, len(password)):
        prefix = password[:split]
        word_part = password[split:]
        word_lower = word_part.lower()
        if word_lower in wordlist:
            rank = wordlist.rank(word_lower)
            case_vars = uppercase_variations(word_part)
            prefix_keyspace = mask_keyspace(prefix)
            guess = rank * case_vars * prefix_keyspace
            best_guess = min(best_guess, guess)

    return best_guess

def mask_keyspace(segment: str) -> int:
    """Compute the keyspace for a mask-described segment.
    Each position contributes its character class size."""
    keyspace = 1
    for c in segment:
        if c.islower():   keyspace *= 26
        elif c.isupper(): keyspace *= 26
        elif c.isdigit():  keyspace *= 10
        else:              keyspace *= 33  # special characters
    return keyspace
```

**Note on infix patterns:** Patterns like `prefix + dict_word + suffix` (e.g., "123monkey!") are not modeled by the hybrid estimator. These are partially covered by the DP decomposition engine, which can combine a brute-force/sequence prefix match with a dictionary match and a brute-force suffix. A dedicated three-part hybrid estimator could be added in a future version if validation shows significant gaps.

### PRINCE (multi-word probability-ordered concatenation)

The PRINCE estimator models the [PRINCE attack](https://hashcat.net/events/p14-trondheim/prince-attack.pdf), which concatenates multiple dictionary words in probability order. Unlike the combinator attack (which concatenates exactly two words), PRINCE supports 2+ words and orders candidates by the product of word frequencies, producing high-probability guesses first.

```python
def estimate_prince_attack(password, wordlist, max_words=4):
    """Try all multi-word splits (2, 3, or 4 words) of the password.

    For each valid split into dictionary words:
      probability = product of word frequencies (freq = 1/rank approximation)
      guess_number = estimated position in PRINCE ordering

    PRINCE ordering differs from combinator in two key ways:
      1. It supports 3+ word splits, not just 2
      2. Candidates are ordered by total probability (product of word freqs),
         not by iterating word1 × word2 sequentially

    The position in PRINCE order is estimated by counting how many multi-word
    combinations have higher total probability."""

    best_guess = float('inf')

    for num_words in range(2, max_words + 1):
        for split_points in generate_splits(password, num_words):
            words = extract_words(password, split_points)
            if not all(w.lower() in wordlist for w in words):
                continue

            ranks = [wordlist.rank(w.lower()) for w in words]

            # PRINCE position estimation:
            # The product of ranks approximates position in probability-sorted order.
            # For 2 words: similar to combinator but with probability ordering.
            # For 3+ words: product of all ranks.
            guess = 1
            for rank in ranks:
                guess *= rank

            # Account for uppercase variations of each word
            for w in words:
                guess *= uppercase_variations(w)

            best_guess = min(best_guess, guess)

    return best_guess

def generate_splits(password, num_words):
    """Generate all ways to split password into num_words non-empty parts.
    Returns lists of split point indices."""
    from itertools import combinations
    n = len(password)
    if num_words > n:
        return
    for split_indices in combinations(range(1, n), num_words - 1):
        yield list(split_indices)

def extract_words(password, split_points):
    """Extract word segments from password given split points."""
    points = [0] + split_points + [len(password)]
    return [password[points[i]:points[i+1]] for i in range(len(points) - 1)]
```

**Separator handling:** Common passphrases use separators between words (e.g., `correct-horse-battery-staple`). The PRINCE estimator handles separators as follows:

```python
SEPARATORS = ['-', '.', '_', ' ', '']  # common passphrase separators + no separator

def estimate_prince_with_separators(password, wordlist, max_words=4):
    """Extended PRINCE estimation that detects and accounts for separators.

    For each candidate separator character:
      1. Split the password on that separator
      2. Check if all segments are dictionary words
      3. Compute guess number as product of ranks × separator_multiplier

    The separator_multiplier accounts for the attacker trying multiple separators.
    With 4 common separators + no separator, the attacker's search space grows by ~5x
    per word boundary, but this is small compared to the dictionary keyspace."""

    best_guess = float('inf')

    for sep in SEPARATORS:
        if sep == '':
            # No separator: fall through to unseparated PRINCE estimation
            guess = estimate_prince_attack(password, wordlist, max_words)
        else:
            parts = password.split(sep)
            if len(parts) < 2 or len(parts) > max_words:
                continue
            if not all(p.lower() in wordlist for p in parts):
                continue

            ranks = [wordlist.rank(p.lower()) for p in parts]
            guess = 1
            for rank in ranks:
                guess *= rank
            for p in parts:
                guess *= uppercase_variations(p)

            # Separator cost is negligible — attacker tries all separators per word combo.

        best_guess = min(best_guess, guess)

    return best_guess
```

### Neural (Monte Carlo CDF estimation)

The neural estimator uses a character-level language model trained on password data to estimate the probability of a given password, then converts that probability to a guess number using a precomputed CDF.

**Model architecture:**
```
Character-level LSTM
  - Vocabulary: 95 printable ASCII characters + start/end tokens (97 total)
  - Embedding dimension: 32
  - Hidden layers: 2 LSTM layers
  - Hidden size: 512 units per layer
  - Output: softmax over vocabulary at each position
  - Training: cross-entropy loss on password corpora (RockYou or similar)
  - Dropout: 0.2 between LSTM layers
```

**Probability computation:**
```python
def neural_password_probability(password, model):
    """Compute P(password) under the neural model.
    P(password) = product of P(char_i | char_1..char_{i-1}) for all positions,
    including the end-of-password token."""
    log_prob = 0.0
    hidden = model.init_hidden()
    prev_char = START_TOKEN
    for char in password + END_TOKEN:
        char_probs, hidden = model.forward(prev_char, hidden)
        log_prob += math.log(char_probs[char])
        prev_char = char
    return math.exp(log_prob)
```

**Monte Carlo guess-number estimation (from CMU):**

The key insight from the [CMU guess-calculator analysis](research/cmu-guess-calculator/report.md) is that a password's guess number under an optimal attacker equals its rank when all passwords are sorted by probability. Since we can't enumerate all passwords, we estimate the rank using Monte Carlo sampling:

```python
def estimate_neural_guess_number(password, model, sample_cdf):
    """Convert neural model probability to an estimated guess number.

    1. Compute P(password) under the model
    2. Look up P in the precomputed sample CDF to find the estimated rank

    The sample CDF is built offline by:
      a. Sampling N passwords from the model (N = 10^7 to 10^8)
      b. Computing P(sample) for each
      c. Sorting by descending probability
      d. Building a (log_prob -> cumulative_count) lookup table
      e. Extrapolating beyond the sample using the observed distribution tail

    At query time, binary search in the CDF table gives the rank estimate.
    """
    prob = neural_password_probability(password, model)
    log_prob = math.log10(prob)

    # Binary search in precomputed CDF: find how many sampled passwords
    # have probability >= this password's probability
    rank = sample_cdf.interpolate(log_prob)
    return rank
```

**CDF precomputation parameters:**
- Sample count: 10^7 minimum, 10^8 for production accuracy
- Storage format: sorted array of `(log10_probability, cumulative_count)` pairs, ~100K entries after binning
- Storage size: ~10 MB for the binned CDF table
- Tail extrapolation: log-linear fit beyond the lowest-probability sample

**Training data:** The model should be trained on a large password corpus (e.g., RockYou 14M passwords). Training details: batch size 128, learning rate 0.001 with Adam optimizer, train for 10-20 epochs until validation loss plateaus. The model file is ~10-50 MB depending on hidden size.

**Note:** The neural estimator is Phase 4 (optional). It requires PyTorch or TensorFlow as an optional dependency, violating the "stdlib + numpy only" core constraint (NFR-011). It should be an optional install: `pip install crack-time[neural]`.

## Estimator Implementation Notes

### Brute Force (whole-password)

The simplest estimator. Determines which character classes are present, sums their sizes to get cardinality, and returns `cardinality^length`. This is the absolute upper bound on crack time — every password has a deterministic brute-force time.

```python
CHARSET_SIZES = {'lower': 26, 'upper': 26, 'digit': 10, 'special': 33}

def brute_force_guesses(analysis: PasswordAnalysis) -> int:
    # cardinality = sum of charset sizes for all groups present in the password
    # e.g. "Hello1" has lower+upper+digit -> 26+26+10 = 62
    return analysis.cardinality ** analysis.length
```

### Dictionary (segment-level)

For each `DictionaryMatch` in the analysis, compute `rank * uppercase_variations * l33t_variations * (2 if reversed)`. Set `match.guesses` to this value. The DP engine selects the best combination of matches.

```python
def dictionary_guesses(match: DictionaryMatch) -> int:
    guesses = match.rank                                    # base: rank in wordlist
    guesses *= uppercase_variations(match.token)            # case multiplier
    if match.reversed:
        guesses *= 2                                        # reversed multiplier
    return max(guesses, 1)

def dictionary_guesses_l33t(match: L33tMatch) -> int:
    guesses = match.rank
    guesses *= uppercase_variations(match.token)
    guesses *= l33t_variations(match.token, match.sub_table)
    return max(guesses, 1)
```

### Mask (whole-password)

Classifies each character position into a character class, then computes the product of per-position class sizes. This models a mask attack (e.g., Hashcat `-a 3` with pattern `?u?l?l?l?l?l?d?d?d?d?s`).

```python
# Hashcat mask character classes
MASK_CLASSES = {
    '?l': 26,    # lowercase
    '?u': 26,    # uppercase
    '?d': 10,    # digit
    '?s': 33,    # special (printable ASCII minus alnum)
    '?a': 95,    # all printable ASCII
}

def char_to_mask_class(c: str) -> str:
    """Map a single character to its Hashcat mask class."""
    if c.islower():   return '?l'
    if c.isupper():   return '?u'
    if c.isdigit():   return '?d'
    return '?s'  # everything else is special

def mask_guesses(password: str) -> int:
    """Compute keyspace for the mask pattern of this password.
    Each position contributes its character class size.
    Example: "Ab1!" -> ?u?l?d?s -> 26 * 26 * 10 * 33 = 222,768"""
    guesses = 1
    for c in password:
        guesses *= MASK_CLASSES[char_to_mask_class(c)]
    return guesses
```

Note: This is strictly less than brute force when the password mixes character classes (mask uses per-position class size; brute force uses the union). A password like "aaa111" has mask keyspace 26^3 * 10^3 = 17.6M vs. brute force keyspace 36^6 = 2.2B. Mask attack wins because the attacker can observe the structural pattern.

**Mask pattern library integration:** The [mask pattern library](06-data-and-models.md#mask-pattern-library-json) (`data/masks/common_masks.json`) contains frequency data from PACK analysis of real breach data, showing how often each mask pattern appears in practice. A real attacker tries the most common masks first, so passwords matching common masks are cracked sooner. The mask estimator should use this library for **attacker-priority-aware estimation**:

```python
def mask_guesses_with_priority(password: str, mask_library: list[dict]) -> int:
    """Compute mask attack guess number accounting for attacker priority ordering.

    A real attacker iterates masks in frequency order (most common first).
    For a password matching mask M at position P in the attacker's priority list,
    the guess number is: sum of keyspaces of all masks tried before M, plus
    the position within mask M's keyspace.

    If the password's mask is not in the library, fall back to pure keyspace
    calculation (the attacker tries it after exhausting all known common masks)."""

    password_mask = ''.join(char_to_mask_class(c) for c in password)
    password_keyspace = mask_guesses(password)

    # mask_library is sorted by descending frequency (attacker tries common first)
    cumulative_guesses = 0
    for entry in mask_library:
        if entry['mask'] == password_mask:
            # Password's mask found in library. Attacker reaches this mask
            # after trying all higher-priority masks. Position within this
            # mask is conservatively estimated as keyspace/2 (average case).
            return cumulative_guesses + password_keyspace // 2
        cumulative_guesses += entry['keyspace']

    # Mask not in library: attacker tries it after all library masks.
    # Fall back to pure keyspace (conservative upper bound).
    return password_keyspace
```

### Date (segment-level)

Detects calendar dates and estimates the search space an attacker would enumerate.

```python
# Constants
YEAR_RANGE = 119          # plausible years: 1900-2019 (zxcvbn range) + nearby years
NUM_DAYS_PER_YEAR = 365   # days in a year (simplified)
SEPARATOR_MULTIPLIER = 4  # no sep, '/', '-', '.' -> 4 options

def date_guesses(match: DateMatch) -> int:
    """Search space for a date pattern.
    An attacker enumerating dates tries:
      ~119 years x 365 days x 4 separator options = ~173,740 combinations."""
    guesses = YEAR_RANGE * NUM_DAYS_PER_YEAR
    if match.has_separator:
        guesses *= SEPARATOR_MULTIPLIER  # attacker tries multiple formats
    return guesses

# Date detection algorithm (in analyzer):
#   For each substring of length 4-10:
#     Try parsing as MMDDYYYY, DDMMYYYY, YYYYMMDD, MMDD, DDMM, MMDDYY, etc.
#     With and without separators (/, -, .)
#     Validate: month in 1-12, day in 1-31, year in 1900-2099
#     If valid: emit DateMatch(i, j, year, month, day, separator, has_separator)
```

### Sequence (segment-level)

Detects constant-delta character sequences (abc, 135, zyx, 2468).

```python
def sequence_guesses(match: SequenceMatch) -> int:
    """Search space for a constant-delta sequence.
    base_guesses: number of possible starting characters.
    Then multiply by length (attacker tries sequences of each length)
    and by 2 if the sequence could go either direction."""
    # Starting character determines the base search space
    if match.token[0].isdigit():
        base_guesses = 10       # digits: 10 possible starts
    elif match.token[0].islower():
        base_guesses = 26       # lowercase: 26 possible starts
    elif match.token[0].isupper():
        base_guesses = 26       # uppercase: 26 possible starts
    else:
        base_guesses = 95       # other (rare): full printable ASCII

    # Short known sequences get a floor
    if match.token in ('0123456789', 'abcdefghij', 'qwertyuiop'):
        base_guesses = 4        # very common, attacker tries these early

    guesses = base_guesses * len(match.token)

    if not match.ascending:
        guesses *= 2            # descending is less common; 2x multiplier

    return max(guesses, 1)

# Sequence detection algorithm (in analyzer):
#   For each starting position i in password:
#     delta = ord(password[i+1]) - ord(password[i])
#     If abs(delta) in {1, 2}: extend forward while delta holds
#     If length >= 3: emit SequenceMatch(i, j, ascending=(delta>0), delta=delta)
```

### Repeat (segment-level)

Detects repeated characters or substrings. Recursively evaluates the base unit.

```python
def repeat_guesses(match: RepeatMatch) -> int:
    """Search space for a repeated pattern.
    Recursively evaluate the base token, then multiply by repeat count.
    Example: 'ababab' -> base 'ab', repeat 3 -> base_guesses * 3"""
    return match.base_guesses * match.repeat_count

# Repeat detection algorithm (in analyzer):
#   Greedy regex: (.+)\1+  -> find longest repeated sequence
#   Lazy regex:   (.+?)\1+ -> find shortest repeating unit
#   For each: compute base_guesses by running the full analyzer on base_token
#   Take whichever produces fewer total guesses
#   Emit RepeatMatch(i, j, base_token, base_guesses, repeat_count)
```

### Uppercase Variation Formula (from zxcvbn)

```python
def uppercase_variations(token: str) -> int:
    if token == token.lower():
        return 1                  # all lowercase -- attacker's default
    if token == token.upper():
        return 2                  # all uppercase -- tried second
    if token[0].isupper() and token[1:] == token[1:].lower():
        return 2                  # first-letter-cap -- very common
    # Mixed case: sum of C(n, k) for k=1..min(U, n-U)
    n = len(token)
    u = sum(1 for c in token if c.isupper())
    return sum(comb(n, k) for k in range(1, min(u, n - u) + 1))
```

### L33t Variation Formula (from zxcvbn)

```python
def l33t_variations(token: str, sub_table: dict[str, str]) -> int:
    """Compute the l33t substitution variation multiplier.

    sub_table maps original_char -> l33t_char, e.g. {'a': '@', 'o': '0'}.
    For each substitution pair, count how many positions in the token use
    the l33t version vs. the original, then compute binomial variations.

    Example: token="p@ssw0rd", sub_table={'a':'@', 'o':'0'}
      For a/@: s=1 (one '@'), u=0 (no 'a' in token) -> sum C(1,1) = 1
      For o/0: s=1 (one '0'), u=0 (no 'o' in token) -> sum C(1,1) = 1
      variations = 1 * 1 = 1, but floor is max(1, 2) = 2
    """
    if not sub_table:
        return 1
    variations = 1
    for original_char, l33t_char in sub_table.items():
        s = sum(1 for c in token if c == l33t_char)    # chars that ARE the l33t version
        u = sum(1 for c in token if c == original_char) # chars that are the ORIGINAL
        if s == 0:
            continue  # this substitution doesn't apply to this token
        variations *= sum(comb(s + u, k) for k in range(1, s + 1))
    return max(variations, 2)       # minimum 2 for any l33t substitution
```

### Keyboard Walk (from zxcvbn)

```python
def spatial_guesses(length: int, turns: int, shifted: int,
                    starting_positions: int, avg_degree: float) -> int:
    guesses = 0
    for L in range(2, length + 1):
        possible_turns = min(turns, L - 1)
        for t in range(1, possible_turns + 1):
            guesses += comb(L - 1, t - 1) * starting_positions * avg_degree ** t

    if shifted > 0:
        s, u = shifted, length - shifted
        if s == 0 or u == 0:
            guesses *= 2
        else:
            guesses *= sum(comb(s + u, k) for k in range(1, min(s, u) + 1))

    return guesses

# QWERTY constants: starting_positions=47, avg_degree=4.595
# Keypad constants: starting_positions=15, avg_degree=5.066
```

## Accuracy Characteristics by Estimator Type

| Estimator Type | Accuracy | Confidence | Best For |
|---------------|----------|------------|----------|
| Brute force | Exact | 100% | Truly random passwords |
| Dictionary rank | Exact (if in wordlist) | 100% | Common words and names |
| Rule inversion | Exact (for supported rules) | ~95% (rule coverage) | Mutated dictionary words |
| Keyboard walk | Exact (small keyspace) | 100% | Spatial patterns |
| PCFG probability | Precomputed table accuracy | Within 2--10x | Structurally typical passwords |
| Markov/OMEN | Level-based approximation | Within 1--2 orders of magnitude | Character-sequence patterns |
| Monte Carlo | Sampling accuracy | Improves with sample size | Neural/complex models |
| Breach lookup | Exact (set membership) | 100% (if in database) | Previously compromised passwords |

The simulator should report confidence levels alongside estimates, distinguishing exact results from approximations.

---

## Match Lifecycle: Analyzer → Estimator → DP

Understanding who creates, owns, and consumes `Match` objects is critical to implementing the pipeline correctly. This section clarifies the flow:

```
Step 1: Analyzer creates Match objects (pattern metadata, no guess counts)
         ↓
Step 2: Segment-level estimators receive matches via PasswordAnalysis,
         compute match.guesses, and return them in EstimateResult.matches
         ↓
Step 3: Orchestrator pools all EstimateResult.matches from all estimators
         ↓
Step 4: DP engine consumes the pooled matches to find optimal decomposition
```

**Detailed flow:**

1. **Analyzer creates matches:** The shared `PasswordAnalyzer` runs all detection steps (dictionary substring matching, keyboard walk detection, sequence detection, date detection, repeat detection, l33t detection). Each detector emits typed `Match` subclass instances (`DictionaryMatch`, `KeyboardWalkMatch`, etc.) with pattern metadata populated (`i`, `j`, `token`, `rank`, `graph`, etc.) but `guesses` set to 0.

2. **Analyzer stores matches in `PasswordAnalysis.matches`:** All detected matches from all detectors are stored in a flat list. This is the canonical source of detected patterns.

3. **Estimators compute guess counts:** Each segment-level estimator iterates over the relevant matches in `analysis.matches` (filtering by type), computes `guesses` for each match using its formula (e.g., `rank * uppercase_variations * l33t_variations` for dictionary), and returns the scored matches in `EstimateResult.matches`. The estimator does **not** modify `analysis.matches` in place — it returns copies or the same objects with `guesses` set.

4. **Orchestrator pools matches:** The orchestrator collects `EstimateResult.matches` from all segment-level estimators into a single pool. If the same substring `[i,j]` is matched by multiple estimators (e.g., dictionary and keyboard walk both match `[0,5]`), both matches appear in the pool with their respective `guesses` values. The DP will select whichever yields fewer total guesses.

5. **DP consumes the pool:** The DP engine takes the pooled matches and finds the optimal non-overlapping decomposition using only `m.i`, `m.j`, and `m.guesses`.

**Key clarification:** `PasswordAnalysis.matches` holds the *detected patterns* (pre-estimation). `EstimateResult.matches` holds the *scored patterns* (post-estimation). The DP consumes only the scored versions.

---

## DP Decomposition Engine

The DP decomposition engine is the architectural centerpiece. It takes all match candidates from all estimators and finds the optimal non-overlapping decomposition that minimizes total guesses.

### Algorithm (adapted from zxcvbn)

```python
def minimum_guess_decomposition(password: str, all_matches: list[Match]) -> DecompositionResult:
    n = len(password)

    # Group matches by ending position
    matches_by_end = defaultdict(list)
    for m in all_matches:
        matches_by_end[m.j].append(m)

    # DP arrays
    min_guesses = [0] * n     # min_guesses[k] = min guesses to cover [0..k]
    best_sequence = [None] * n  # the optimal match sequence ending at k
    last_guess = [0] * n       # guesses of last match in optimal sequence

    for k in range(n):
        # Default: brute-force the entire prefix [0..k]
        bf = bruteforce_guesses(password[:k+1])
        min_guesses[k] = bf
        best_sequence[k] = [BruteforceMatch(0, k)]
        last_guess[k] = bf

        # Try each match ending at position k
        for m in matches_by_end[k]:
            g = m.guesses
            if m.i == 0:
                total = g  # Match covers from the start
            else:
                total = min_guesses[m.i - 1] * g  # Combine with optimal prefix

            if total < min_guesses[k]:
                min_guesses[k] = total
                if m.i == 0:
                    best_sequence[k] = [m]
                else:
                    best_sequence[k] = best_sequence[m.i - 1] + [m]
                last_guess[k] = g

    return DecompositionResult(
        guesses=min_guesses[n - 1],
        sequence=best_sequence[n - 1],
        log10_guesses=math.log10(max(min_guesses[n - 1], 1))
    )
```

### Integration with Estimators

Segment-level estimators produce typed `Match` subclass instances (`DictionaryMatch`, `KeyboardWalkMatch`, `SequenceMatch`, `DateMatch`, `RepeatMatch`, `L33tMatch` — defined in [Implementation Roadmap](07-implementation-roadmap.md)). Each match has `{i, j, guesses, pattern, token}` plus type-specific metadata. All matches from all segment-level estimators are pooled and fed into the DP. The DP doesn't care which estimator produced a match — it just uses `m.i`, `m.j`, and `m.guesses` to pick the combination that minimizes total guesses.

This means:
- A dictionary match at [0,7] competes with a keyboard walk at [0,7] for the same substring
- The DP may mix match types: dictionary at [0,5] + brute-force at [6,7] + date at [8,11]
- Adding a new estimator automatically improves decomposition quality — it just adds more match candidates

### Estimator Classification: Segment-Level vs. Whole-Password

Each estimator is classified as either **segment-level** (produces `Match` objects fed into the DP) or **whole-password** (produces a single guess number for the entire password). The final crack time is:

```
final_guesses = min(
    dp_optimal_decomposition_guesses,   # best segmentation from all segment-level matches
    markov_guesses,                      # whole-password
    pcfg_guesses,                        # whole-password
    breach_guesses,                      # whole-password (0 if found)
    neural_guesses,                      # whole-password
    brute_force_guesses                  # whole-password (always available as upper bound)
)
```

| Estimator | Type | Rationale |
|-----------|------|-----------|
| Dictionary | Segment-level | Matches substrings; DP combines with other segments |
| L33t dictionary | Segment-level | Same as dictionary, after de-substitution |
| Keyboard walk | Segment-level | Matches substrings of spatial patterns |
| Sequence | Segment-level | Matches substrings of constant-delta runs |
| Date | Segment-level | Matches 4-10 character date substrings |
| Repeat | Segment-level | Matches repeated substrings |
| Rule-based | Whole-password | Inverts rules against the entire password |
| Combinator | Whole-password | Tries all 2-word splits of the full password |
| Hybrid | Whole-password | Tries dictionary + suffix/prefix on full password |
| PRINCE | Whole-password | Tries multi-word splits of the full password |
| Mask | Whole-password | Evaluates the full password's structural mask |
| PCFG | Whole-password | Computes grammar probability for full password |
| Markov/OMEN | Whole-password | Computes n-gram probability for full password |
| Breach lookup | Whole-password | Checks full password against breach set |
| Neural | Whole-password | Computes model probability for full password |
| Brute force | Whole-password | Always `cardinality^length` for full password |

**Orchestration flow:**

1. Analyzer runs → produces `PasswordAnalysis` with all segment-level matches
2. All estimators run → segment-level ones add matches to the pool, whole-password ones return a guess number
3. DP engine runs on the pooled segment-level matches → produces `dp_guesses`
4. Final result = `min(dp_guesses, *all_whole_password_guesses)`

Note: Some whole-password estimators (combinator, hybrid, PRINCE) *could* be segment-level in a future version, but starting them as whole-password is simpler and correct — the DP's brute-force fallback covers any unmatched segments.

---

See also: [Architecture](04-architecture.md) | [Data & Models](06-data-and-models.md) | [Validation Strategy](08-validation-strategy.md)

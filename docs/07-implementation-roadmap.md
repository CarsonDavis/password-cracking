# Implementation Roadmap

Four-phase plan to build the Password Crack-Time Simulator, from core framework to neural estimator.

---

## Phase 1: Core Framework + Analytical Estimators

**Goal:** Working CLI that handles the most common passwords using deterministic methods.

### Deliverables

**1. Project scaffolding**
- `pyproject.toml`, package structure, pytest setup
- `Estimator` base class with `estimate(analysis: PasswordAnalysis) -> EstimateResult`
- `PasswordAnalysis` data class (tokenized segments, detected patterns, character properties)

**2. Shared password analyzer**
- Character class detection (digits, lower, upper, special, unicode)
- Keyboard walk detection (QWERTY adjacency graph from zxcvbn)
- Sequence detection (abc, 123, constant-delta runs)
- Date detection (with/without separators, multiple formats)
- Repeat detection (greedy + lazy regex, recursive base evaluation)

**3. Analytical estimators**
- Brute force: `charset^length`
- Dictionary: Substring matching against frequency-ranked wordlist; `rank * uppercase_vars * l33t_vars`
- L33t-aware dictionary matching: Substitution table from zxcvbn, enumerate de-l33t variants, check against dictionary, binomial coefficient variation counting (FR-025, Must priority)
- Keyboard walk: Spatial formula from zxcvbn (`starting_positions * avg_degree^turns * shift_vars`)
- Mask: Match against common mask patterns, compute keyspace
- Date: `year_space * 365 * separator_multiplier`
- Sequence: `base_start * length * direction_multiplier`
- Repeat: Recursive evaluation of base pattern, `guesses = base_guesses * repeat_count` (FR-012, Must priority)

**4. DP decomposition engine**
- Port zxcvbn's minimum-cost DP from CoffeeScript to Python
- Run all matchers (over-generate), then find optimal non-overlapping decomposition
- Cost = product of per-segment guesses

**5. Hardware calculator**
- Hash rate lookup table (from [benchmarks report](research/password-cracking-benchmarks/report.md))
- Hardware tier multipliers
- `crack_time = guess_number / effective_hash_rate`
- bcrypt cost factor conversion formula

**6. CLI**
- `crack-time estimate <password> --hash <algorithm> --hardware <tier>`
- JSON and human-readable output modes
- Batch mode: `crack-time batch <password-file>` for evaluating password sets

**6b. Phase 1 unit tests**
- Unit tests for every Phase 1 estimator against known-answer test cases (see [Validation Strategy](08-validation-strategy.md))
- Unit tests for the DP decomposition engine with hand-crafted match sets
- Unit tests for the hardware calculator (known hash rate × known tier = expected value)
- Integration test: full pipeline on at least 10 reference passwords from the test case table
- *Note: The comprehensive validation suite (deliverable #22, Phase 4) includes cross-tool comparison and ground-truth Hashcat runs. But basic unit testing must happen in each phase alongside the code it validates — do not defer all testing to Phase 4.*

### Phase 1 Interfaces

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

# --- Match / pattern types (used by analyzer AND DP engine) ---

@dataclass
class Match:
    """A detected pattern covering password[i..j] (inclusive).
    Produced by the analyzer; consumed by estimators and the DP engine."""
    pattern: str           # 'dictionary', 'spatial', 'sequence', 'date',
                           # 'repeat', 'l33t', 'brute_force'
    token: str             # The substring password[i..j+1]
    i: int                 # Start index (inclusive)
    j: int                 # End index (inclusive)
    guesses: int           # Estimated guesses for this match (set by estimator)

@dataclass
class DictionaryMatch(Match):
    """Substring found in a frequency-ranked wordlist."""
    word: str = ""              # Matched word (lowercase)
    rank: int = 0               # 1-based rank in wordlist
    dictionary_name: str = ""   # 'common_passwords', 'english', 'names', 'surnames', 'user'
    reversed: bool = False      # True if matched after reversing the token

@dataclass
class L33tMatch(Match):
    """Dictionary match found after de-l33t substitution."""
    word: str = ""              # Original (de-l33ted) word
    rank: int = 0               # Rank in wordlist
    dictionary_name: str = ""
    sub_table: dict = field(default_factory=dict)
    # sub_table maps original_char -> l33t_char for this token, e.g. {'a': '@', 'o': '0'}
    # count_substituted(char) = number of positions where char was l33ted
    # count_unsubstituted(char) = number of positions where char was NOT l33ted

@dataclass
class KeyboardWalkMatch(Match):
    """Spatial pattern on a keyboard adjacency graph."""
    graph: str = ""             # 'qwerty', 'dvorak', 'keypad'
    turns: int = 0              # Number of direction changes in the walk
    shifted_count: int = 0      # Number of shifted (uppercase/symbol) characters

@dataclass
class SequenceMatch(Match):
    """Constant-delta character sequence (abc, 135, zyx)."""
    sequence_name: str = ""     # 'lower', 'upper', 'digit', 'unicode'
    ascending: bool = True      # True if delta > 0
    delta: int = 0              # Character code delta between adjacent chars

@dataclass
class DateMatch(Match):
    """Calendar date pattern."""
    year: int = 0
    month: int = 0
    day: int = 0
    separator: str = ""         # '/', '-', '.', or '' (no separator)
    has_separator: bool = False

@dataclass
class RepeatMatch(Match):
    """Repeated character or subsequence."""
    base_token: str = ""                        # The repeating unit
    base_guesses: int = 0                       # Guesses for the base (from recursive analysis)
    repeat_count: int = 0                       # Number of repetitions

# --- Analysis result ---

@dataclass
class PasswordAnalysis:
    """Shared analysis result, computed once per password.
    All estimators receive this; the DP engine uses the matches list."""
    password: str
    length: int
    charsets: set[str]                          # {'lower', 'upper', 'digit', 'special'}
    cardinality: int                            # Sum of charset sizes present (e.g. lower+upper+digit = 62)
    matches: list[Match] = field(default_factory=list)  # ALL detected matches (all types)
    pcfg_structure: str | None = None           # L/D/S tokenization (e.g., "L6D2S1")
    # Note: pcfg_structure is populated by analyzer step [8] but consumed only by
    # the PCFG estimator (Phase 2). Included here as a forward-looking field so the
    # PasswordAnalysis interface remains stable across phases. In Phase 1, the analyzer
    # MAY populate this field or leave it as None — the PCFG estimator is not yet active.

# Convenience accessors:
#   analysis.matches_of_type('dictionary')  -> list[DictionaryMatch]
#   analysis.matches_of_type('spatial')     -> list[KeyboardWalkMatch]
# Alternatively, filter by isinstance().

# --- Estimator interface ---

@dataclass
class EstimateResult:
    """Result from a single estimator."""
    guess_number: int | float    # float('inf') if not applicable
    attack_name: str             # Human-readable attack description
    details: dict                # Estimator-specific metadata
    matches: list[Match] = field(default_factory=list)
    # Segment-level estimators populate matches (fed into DP).
    # Whole-password estimators leave matches empty.

class Estimator(ABC):
    @abstractmethod
    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        """Estimate guess number for this attack strategy.
        The password string is available via analysis.password."""
        ...
```

**Note on cardinality:** `cardinality` is the size of the *character set the attacker must assume* to brute-force this password. It is the sum of charset group sizes for all groups present: if the password contains lowercase and digits, cardinality = 26 + 10 = 36. The groups are: lower (26), upper (26), digit (10), special (33), giving a maximum of 95 for printable ASCII.

**Note on matches:** All detected patterns are stored as typed `Match` subclass instances in a single flat list (`analysis.matches`). The DP engine consumes this list directly. Estimators that produce segment-level matches (dictionary, keyboard walk, sequence, date, repeat, l33t) return them in `EstimateResult.matches` so the orchestrator can pool them before running the DP. Whole-password estimators (brute force, Markov, PCFG, breach) set `EstimateResult.guess_number` directly and leave `matches` empty.

### Phase 1 Hardware Calculator

See [Architecture — Hardware Calculator](04-architecture.md#hardware-calculator) for the full implementation including `HARDWARE_TIERS` dict, `crack_time_seconds()`, and `bcrypt_hash_rate()` derivation. The tier multipliers are pre-baked (already incorporate multi-GPU scaling losses), so the calculator is a simple lookup:

```python
def crack_time_seconds(guess_number: int, algorithm: str, hardware_tier: str) -> float:
    base_rate = resolve_hash_rate(algorithm)  # handles bcrypt cost derivation
    multiplier = HARDWARE_TIERS[hardware_tier]["multiplier"]
    effective_rate = base_rate * multiplier
    if effective_rate == 0:
        return float('inf')
    return guess_number / effective_rate

def resolve_hash_rate(algorithm: str) -> float:
    """Look up base hash rate. For bcrypt with arbitrary cost, derive from cost=5."""
    if algorithm in HASH_RATES_PER_GPU:
        return HASH_RATES_PER_GPU[algorithm]
    # Handle bcrypt_costN for any N
    if algorithm.startswith("bcrypt_cost"):
        cost = int(algorithm.removeprefix("bcrypt_cost"))
        return HASH_RATES_PER_GPU["bcrypt_cost5"] / (2 ** (cost - 5))
    raise ValueError(f"Unknown algorithm: {algorithm}")
```

---

## Phase 2: Probabilistic Estimators + Rule Inversion

**Goal:** Add the major attacks that require external data or models.

### Deliverables

**7. Breach lookup estimator**
- Bloom filter or sorted binary search over HIBP Pwned Passwords
- If match: guess_number = 0 (instant crack)

**8. Rule inversion estimator**
- Port UChicago's rule inversion architecture
- Parse Hashcat rule syntax (at minimum: best64.rule)
- Implement `apply()` and `invert()` for common operations (l, u, c, $X, ^X, r, sXY, DN, iNX, oNX, TN, d, [, ])
- Compute guess number using rule_idx x wordlist_size + word_pos

**9. Combinator estimator**
- Try all split points; check both halves against wordlist
- Guess = rank_left x wordlist_size + rank_right

**10. Hybrid estimator**
- Try splitting password into (dictionary_word, suffix/prefix)
- Estimate suffix keyspace from character classes
- Guess = dict_rank x suffix_keyspace

**11. PCFG estimator**
- Integrate with pcfg_cracker's grammar format
- Parse password into PCFG structure (L/D/S/K/Y segments)
- Compute P(password) from grammar tables
- Build precomputed lookup table (log_prob -> guess_number)
- Binary search interpolation at query time

**12. Markov/OMEN estimator**
- Port OMEN's 4-component model (IP + CP + EP + LN)
- Implement level computation and level-count accumulation
- Additive smoothing with configurable delta
- Default n-gram order 4

**13. ~~L33t-aware dictionary matching~~ (Moved to Phase 1, deliverable #3)**
- *L33t-aware dictionary matching is now part of Phase 1 analytical estimators (FR-025, Must priority). The analyzer already detects l33t substitutions in Phase 1 step [3]; the matching logic belongs alongside it to avoid producing detection output with no consumer.*

**14. Improved DP decomposition**
- Integrate new estimators as match sources for the DP
- Handle rule-based matches, PCFG structural matches, Markov probability matches

### Phase 2 Rule Operation Interface

```python
class RuleOp(ABC):
    """Single primitive rule operation (e.g., $1, c, sa@)."""

    @abstractmethod
    def apply(self, word: str) -> str:
        """Forward application of this operation."""
        ...

    @abstractmethod
    def invert(self, target: str) -> set[str]:
        """Given target, return set of possible inputs that produce it."""
        ...

class AppendChar(RuleOp):
    def __init__(self, char: str):
        self.char = char

    def apply(self, word: str) -> str:
        return word + self.char

    def invert(self, target: str) -> set[str]:
        if target.endswith(self.char):
            return {target[:-1]}
        return set()

class SubstituteChar(RuleOp):
    def __init__(self, old: str, new: str):
        self.old, self.new = old, new

    def apply(self, word: str) -> str:
        return word.replace(self.old, self.new)

    def invert(self, target: str) -> set[str]:
        # Each occurrence of self.new could have been self.old or already self.new
        positions = [i for i, c in enumerate(target) if c == self.new]
        results = set()
        for combo in itertools.product([self.old, self.new], repeat=len(positions)):
            chars = list(target)
            for pos, replacement in zip(positions, combo):
                chars[pos] = replacement
            results.add(''.join(chars))
        return results
```

### Phase 2 PCFG Probability Computation

```python
def pcfg_probability(password: str, grammar) -> float:
    segments = grammar.parse(password)
    # e.g., [("L", "monkey"), ("D", "69"), ("S", "!")]
    if segments is None:
        return 0.0

    structure = "".join(f"{t}{len(v)}" for t, v in segments)
    # e.g., "L6D2S1"

    p = grammar.structure_prob(structure)
    if p == 0:
        return 0.0

    for seg_type, seg_value in segments:
        if seg_type == "L":
            p *= grammar.alpha_prob(seg_value.lower(), len(seg_value))
            p *= grammar.cap_mask_prob(extract_cap_mask(seg_value), len(seg_value))
        elif seg_type == "D":
            p *= grammar.digit_prob(seg_value, len(seg_value))
        elif seg_type == "S":
            p *= grammar.special_prob(seg_value, len(seg_value))
        elif seg_type == "K":
            p *= grammar.keyboard_prob(seg_value, len(seg_value))

    return p
```

---

## Phase 3: Advanced Estimators + Polish

**Goal:** Coverage of remaining attack types and usable output.

### Deliverables

**15. PRINCE estimator**
- Multi-word decomposition (try 2- and 3-word splits)
- Probability = product of word frequency ranks
- Probability-ordered position estimation

**16. ~~Repeat/pattern estimator~~ (Moved to Phase 1, deliverable #3)**
- *Repeat estimation is now part of Phase 1 analytical estimators (FR-012, Must priority). The analyzer already detects repeats in Phase 1 step [7]; the estimation formula (`base_guesses * repeat_count`) is trivial and should not be deferred.*

**17. Attacker profiles**
- Predefined profiles: "script_kiddie" (Phase 1--2 techniques only), "professional" (all phases), "nation_state" (all + massive hardware)
- Each profile selects which estimators run and which hardware tier applies

**18. Context inputs**
- Accept optional user context: username, email, site name, birthdate
- Add to dictionary as rank-1 entries (per zxcvbn pattern)
- Flag password components that match context

**19. Output formatting**
- Human-readable summary with explanation of weakest decomposition
- JSON output with full per-strategy breakdown
- Color-coded strength rating (0--4 scale, adapted from zxcvbn thresholds)

**20. Data packaging**
- Bundle default wordlist, keyboard graphs, rule files, hash rates
- Download script for optional large assets (PCFG grammar, Markov tables, breach Bloom filter)

---

## Phase 4: Neural Estimator + Validation

**Goal:** Optional neural coverage and rigorous validation.

### Deliverables

**21. Neural password model (optional)**
- Character-level LSTM trained on password data
- Monte Carlo guess-number estimation (sample CDF approach from CMU)
- Plugs into the min-auto ensemble as one more estimator

**22. Validation suite**
- Unit tests for every estimator against known answers
- Integration test: full pipeline on reference passwords
- Benchmark comparison: results vs. Hive Systems 2025 tables
- Tool comparison: results vs. zxcvbn scores on the same passwords
- Ground truth: run actual Hashcat on a test set, compare predicted vs. actual crack times

**23. Guessability curve generation**
- Given a password set, produce CDF curves (guess number vs. % cracked)
- Compare across strategies and against published results
- Matplotlib-based plotting utility

**24. Documentation**
- Algorithm documentation for each estimator
- Data source attribution
- Usage guide with examples
- API reference

---

See also: [Architecture](04-architecture.md) | [Estimator Specs](05-estimator-specs.md) | [Validation Strategy](08-validation-strategy.md)

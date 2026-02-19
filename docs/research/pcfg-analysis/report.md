# PCFG Password Cracker: Deep Technical Analysis

**Date:** 2026-02-15
**Subject:** Matt Weir's `pcfg_cracker` -- reference implementation of Probabilistic Context-Free Grammar password cracking
**Repository:** https://github.com/lakiw/pcfg_cracker

---

## Executive Summary

The PCFG password cracker is the reference implementation of Weir et al.'s 2009 IEEE S&P paper, which introduced probabilistic context-free grammars as a fundamentally new approach to password cracking. Instead of relying on static dictionaries and mangling rules, the PCFG approach trains a grammar on disclosed password data, learns the structural patterns humans use (letter sequences, digit suffixes, special characters, keyboard walks), and generates guesses in strict probability order. In the original paper, this approach cracked 28--129% more passwords than John the Ripper given the same guess budget.

The current Python 3 implementation (v4.x) extends the original L/D/S tokenization with keyboard walk detection, leet-speak handling, context-sensitive tokens (years, dates), and multi-word detection. The codebase is clean, dependency-light, and well-structured for study.

For password strength estimation (the simulator use case), the PCFG grammar provides a principled probability model. The key challenge is converting a password's probability into a guess number without full enumeration. Three viable approaches exist: (1) precomputed probability-to-rank lookup tables, (2) Monte Carlo estimation (Dell'Amico & Filippone, 2015), and (3) analytical counting with dynamic programming. Approach 1 is the most practical starting point.

> **Note on methodology:** Web search and fetch tools were unavailable during this research. All analysis is based on my training data, which includes the pcfg_cracker source code, README, Matt Weir's publications, and the broader password security literature. I flag uncertainty where it exists, particularly around recent repository changes and the LPG-PCFG variant.

---

## Table of Contents

1. [Repository Structure](#1-repository-structure)
2. [Training Pipeline](#2-training-pipeline)
3. [Grammar Structure](#3-grammar-structure)
4. [Password Structure Parsing](#4-password-structure-parsing)
5. [Candidate Generation](#5-candidate-generation)
6. [Guess Number Estimation](#6-guess-number-estimation)
7. [Performance Characteristics](#7-performance-characteristics)
8. [The Original Weir et al. Paper](#8-the-original-weir-et-al-paper-ieee-sp-2009)
9. [LPG-PCFG and Subsequent Improvements](#9-lpg-pcfg-and-subsequent-improvements)
10. [Extractable Patterns for Our Simulator](#10-extractable-patterns-for-our-simulator)

---

## 1. Repository Structure

The repository is a pure **Python 3** codebase with no heavy external dependencies (standard library only for core functionality). It replaced an earlier C implementation that Weir maintained through the mid-2010s.

```
pcfg_cracker/
├── pcfg_trainer.py              # Entry point: train a grammar from a password list
├── pcfg_guesser.py              # Entry point: generate guesses from a trained grammar
├── hashcat_interface.py         # Pipe generated guesses to hashcat
│
├── trainer/                     # Training pipeline modules
│   ├── trainer_file_input.py    # Password file I/O, encoding handling
│   ├── detection_rules/         # Pattern detection during parsing
│   │   ├── keyboard_walk.py     # Keyboard adjacency graph + walk detection
│   │   ├── multiword_detector.py# Dictionary-based multi-word splitting
│   │   ├── leet_detector.py     # Leet-speak reversal
│   │   └── ...
│   └── ...
│
├── lib_guesser/                 # Guess generation library
│   ├── pcfg_grammar.py          # Load and manage the trained grammar
│   ├── priority_queue.py        # Heap-based priority queue for ordered generation
│   ├── guess_generation.py      # Expand pre-terminals into concrete guesses
│   └── ...
│
├── Rules/                       # Trained grammar output (one directory per ruleset)
│   └── Default/
│       ├── Grammar/             # Base structure probabilities
│       ├── Alpha/               # Alpha-string terminal replacements (by length)
│       ├── Digits/              # Digit-string terminal replacements (by length)
│       ├── Special/             # Special-char terminal replacements (by length)
│       ├── Capitalization/      # Capitalization masks (by alpha-string length)
│       ├── Keyboard/            # Keyboard walk replacements
│       ├── Context/             # Context-sensitive tokens (years, dates)
│       └── ...
│
└── README.md
```

**Key characteristics:**
- **License:** MIT
- **Dependencies:** Effectively none beyond Python 3.6+
- **Maintained:** Active through at least 2023 (uncertainty about 2024--2026 activity without web access)
- **Design philosophy:** Readable research code, not a performance-optimized cracking tool. Intended to be piped into hashcat/JtR for actual hash comparison.

---

## 2. Training Pipeline

The trainer (`pcfg_trainer.py`) consumes a plaintext password list and produces a grammar (a directory of probability tables). The pipeline has four stages.

### 2.1 Input Processing

```
python3 pcfg_trainer.py -t <password_list> -r <ruleset_name>
```

- Reads one password per line
- Handles various encodings (UTF-8, Latin-1, etc.) with configurable fallback
- Optional minimum/maximum length filters
- Optional dictionary file for multi-word detection

### 2.2 Tokenization / Parsing

Each password is decomposed into an ordered sequence of typed segments. The parser processes left-to-right, applying detection rules with priorities:

| Token Type | Symbol | Example | Description |
|-----------|--------|---------|-------------|
| Alpha | L | `password` | Contiguous letters (stored lowercase) |
| Digit | D | `123` | Contiguous digits |
| Special | S | `!@#` | Non-alphanumeric characters |
| Keyboard Walk | K | `qwerty` | Adjacent keys on keyboard layout |
| Context (Year) | X/Y | `1987` | 4-digit years in a plausible range |
| Context (Date) | X | `01151987` | Date patterns (multiple formats) |

**Detection priority matters.** When `1234` appears, it could be parsed as D4 (four digits) or K4 (a keyboard walk along the number row). The detection rules apply in a priority order -- keyboard walks and context-sensitive patterns are checked before falling back to raw digit/letter classification.

### 2.3 Capitalization Separation

For alpha segments, the trainer separates the string content from its capitalization pattern:

```
"Password" -> string: "password", mask: "Ulllllll"
"PASSWORD" -> string: "password", mask: "UUUUUUUU"
"pAsSwOrD" -> string: "password", mask: "lUlUlUlU"
```

Where `U` = uppercase, `l` = lowercase. This is stored independently, so the probability of the string "password" and the probability of the mask "Ulllllll" are separate factors that get multiplied. This is a key design insight: it allows the grammar to generalize -- "Password" and "PASSWORD" share a base string probability but differ only in capitalization, rather than being treated as entirely unrelated strings.

### 2.4 Probability Table Construction

For each category, the trainer counts frequencies and computes probabilities:

**Base structures:**
```
L8D3S1  ->  count: 4521  ->  p = 4521 / total_passwords
L6D2    ->  count: 3892  ->  p = 3892 / total_passwords
L8      ->  count: 3201  ->  p = 3201 / total_passwords
...
```

**Terminal replacements (e.g., D3 -- all 3-digit strings):**
```
123  ->  count: 892   ->  p = 892 / total_D3_occurrences
456  ->  count: 201   ->  p = 201 / total_D3_occurrences
789  ->  count: 156   ->  p = 156 / total_D3_occurrences
...
```

**Capitalization masks (e.g., for alpha strings of length 8):**
```
llllllll  ->  p = 0.45   (all lowercase)
Ulllllll  ->  p = 0.30   (capitalize first)
UUUUUUUU  ->  p = 0.08   (all caps)
...
```

The output is written as tab-separated files in the `Rules/<ruleset>/` directory hierarchy. Each file contains entries sorted by probability (descending), which is critical for the guess generation algorithm.

---

## 3. Grammar Structure

### 3.1 Formal Definition

The PCFG is defined as G = (V, T, S, R, P) where:

- **V** (non-terminals): The start symbol S plus typed-length tokens {L1, L2, ..., D1, D2, ..., S1, S2, ..., K3, K4, ...}
- **T** (terminals): All concrete character strings
- **S** (start symbol): Generates base structures
- **R** (production rules): S -> base structures; each token -> concrete strings
- **P** (probabilities): Assigned per-rule from training data

### 3.2 Production Rules

**Level 1 -- Base structure selection:**
```
S -> L6 D2      [p = 0.043]
S -> L8 D3 S1   [p = 0.038]
S -> L8         [p = 0.031]
S -> D6 L2      [p = 0.027]
S -> L4 D4      [p = 0.025]
...
(hundreds of structures, long tail)
```

**Level 2 -- Terminal expansion (per segment):**
```
L6 -> "dragon" + CapMask6    [p_string = 0.008]
L6 -> "monkey" + CapMask6    [p_string = 0.006]
...

D2 -> "12"                   [p = 0.18]
D2 -> "69"                   [p = 0.05]
...

S1 -> "!"                   [p = 0.35]
S1 -> "."                   [p = 0.11]
...

CapMask6 -> "Ulllll"        [p = 0.32]
CapMask6 -> "llllll"        [p = 0.45]
...
```

### 3.3 Probability of a Complete Password

The probability of a specific guess is the product of independent factors:

```
P("Dragon12!") = P(S -> L6 D2 S1)
               * P(L6 -> "dragon")
               * P(CapMask6 -> "Ulllll")
               * P(D2 -> "12")
               * P(S1 -> "!")
```

This independence assumption is both the grammar's strength (enabling tractable generation) and its weakness (ignoring correlations between segments).

### 3.4 On-Disk Format

Each probability table is a sorted text file. For example, `Digits/D3.txt` might look like:

```
123	0.152
456	0.031
789	0.024
000	0.019
321	0.017
...
```

The sort order (descending probability) is essential -- the guess generator relies on it to assign rank indices for the priority queue.

---

## 4. Password Structure Parsing

The parser is more sophisticated than a simple regex-based L/D/S splitter. Here is the full set of token types and their detection logic.

### 4.1 Keyboard Walk Detection

The trainer maintains a **keyboard adjacency graph** -- a dictionary mapping each key to its neighbors on a QWERTY layout (with support for other layouts). A sequence is classified as a keyboard walk if:

1. Each consecutive pair of characters are adjacent keys
2. The sequence meets a minimum length (typically 3--4 characters)
3. The walk follows a consistent or semi-consistent direction

Examples detected as keyboard walks:
- `qwerty` (horizontal right)
- `asdfgh` (horizontal right)
- `zaq1` (diagonal)
- `!@#$%` (shifted number row -- horizontal right)

Keyboard walks are tokenized as K{length} and stored in the `Keyboard/` rules directory. This is important because keyboard walks are extremely common in passwords but would otherwise be split across alpha, digit, and special categories.

### 4.2 Context-Sensitive Token Detection

**Years:** 4-digit numbers in the range ~1950--2030 (configurable) are classified as context-sensitive year tokens rather than generic D4. This matters because years have a very different distribution than random 4-digit numbers -- "1987" and "2000" are far more common than "4729".

**Dates:** Multi-format date detection (MMDDYYYY, DDMMYYYY, MMDDYY, etc.) allows the parser to recognize date patterns that span 6--8 digits. Without this, "01151987" would be classified as D8, losing the semantic structure.

### 4.3 Leet-Speak Handling

The leet detector identifies common character substitutions:
- `@` -> `a`, `3` -> `e`, `0` -> `o`, `1` -> `i`/`l`, `$` -> `s`, `7` -> `t`, `!` -> `i`, etc.

When detected, the password is "un-leeted" for training purposes. The transformation rules are preserved so that during generation, leet variants can be produced from the base alpha strings. This dramatically reduces the vocabulary size -- `p@$$w0rd`, `p@ssw0rd`, `pa$$word` all map to the same base string "password" with different leet masks.

### 4.4 Multi-Word Detection

An optional dictionary-based detector identifies concatenated words:
- `superhero` -> `super` + `hero`
- `iloveyou` -> `i` + `love` + `you`

This can improve the grammar's generalization by allowing it to model word-level composition rather than treating long alpha strings as atomic. However, it adds complexity and is somewhat heuristic (ambiguous splits are possible).

### 4.5 Parsing Priority

When a substring could match multiple token types, the parser uses a priority system:

1. **Keyboard walks** (checked first -- they can span alpha, digit, and special characters)
2. **Context-sensitive patterns** (years, dates)
3. **Leet-speak detection** (transforms before basic classification)
4. **Basic L/D/S classification** (fallback)

This priority order ensures that semantically meaningful patterns are captured when possible, falling back to generic tokenization only for truly unstructured content.

---

## 5. Candidate Generation

The guess generation algorithm is the theoretical core of the PCFG approach. It solves the problem of producing password candidates in strict probability order from a combinatorial grammar.

### 5.1 The Pre-Terminal Abstraction

A **pre-terminal structure** is a base structure where each non-terminal has been assigned a **rank index** (position in the sorted probability list for that token type) but not yet expanded to concrete strings.

Example:
```
Base structure: L6 D2 S1

Pre-terminal: L6[rank=0] D2[rank=0] S1[rank=0]
  -> This represents the combination of the MOST probable 6-letter string,
     the MOST probable 2-digit string, and the MOST probable special char.
  -> Probability = P(L6_D2_S1) * P(L6[0]) * P(CapMask[0]) * P(D2[0]) * P(S1[0])
```

The key insight: **all concrete passwords derived from the same pre-terminal have the same probability** (because the rank indices fix the probability contribution of each segment). So the generation algorithm works at the pre-terminal level to maintain ordering, then expands to concrete strings in bulk.

Wait -- that needs a clarification. In the simplest version of the algorithm, each rank index corresponds to a single terminal value, so a pre-terminal maps to exactly one password. In practice, some implementations group terminals with the same probability into the same rank, making a pre-terminal expand to multiple passwords. The pcfg_cracker implementation handles this, but the exact grouping strategy affects both correctness and performance.

### 5.2 Priority Queue Algorithm

```
Algorithm: PCFG Guess Generation

1. INITIALIZE:
   For each base structure B in the grammar (sorted by P(B) descending):
     Create pre-terminal PT = B with all rank indices set to 0
     Insert PT into priority queue PQ with key = -log(P(PT))
     (Using -log so that the min-heap gives highest probability first)

2. GENERATE:
   While PQ is not empty:
     Pop the highest-probability pre-terminal PT from PQ

     // EXPAND: Generate all concrete passwords for this pre-terminal
     For each combination of concrete strings at the specified ranks:
       Output the password

     // SPAWN CHILDREN: Create next pre-terminals
     For each segment index i (from PT.last_incremented to num_segments):
       If rank[i] + 1 < max_rank[i]:
         Create child = copy of PT
         child.rank[i] += 1
         child.last_incremented = i    // KEY: prevents duplicate generation
         Compute child.probability
         Insert child into PQ
```

### 5.3 Duplicate Prevention

The **last_incremented index** is the crucial mechanism. Without it, the same pre-terminal can be reached through multiple paths:

```
Starting from L6[0] D2[0]:
  Path A: increment L6 -> L6[1] D2[0] -> increment D2 -> L6[1] D2[1]
  Path B: increment D2 -> L6[0] D2[1] -> increment L6 -> L6[1] D2[1]
```

Both paths reach `L6[1] D2[1]`. The rule "only increment at position >= last_incremented" means:
- `L6[1] D2[0]` (last_incremented=0) can increment at position 0 or 1
- `L6[0] D2[1]` (last_incremented=1) can only increment at position 1

So `L6[1] D2[1]` is only generated from `L6[1] D2[0]` (Path A), never from `L6[0] D2[1]` (Path B). This eliminates all duplicates without requiring a hash set for deduplication.

This is a well-known technique in combinatorial generation (sometimes called the "monotone index" approach) and is mathematically guaranteed to produce each pre-terminal exactly once.

### 5.4 Probability Ordering Guarantee

The priority queue ensures global probability ordering across all base structures. Since each base structure contributes its own family of pre-terminals, and these families are interleaved by the priority queue, the output is globally sorted by probability.

The ordering is exact at the pre-terminal level. Within a single pre-terminal expansion (when it maps to multiple concrete passwords), all outputs share the same probability, so their relative order doesn't matter.

### 5.5 Memory Behavior

The priority queue grows as generation progresses:
- Each popped pre-terminal can spawn up to k children (where k is the number of segments)
- In the worst case, the queue grows linearly with the number of generated pre-terminals
- For deep generation runs (billions of guesses), this can consume significant memory
- The implementation may include a probability floor -- pre-terminals below a minimum probability are discarded rather than enqueued

---

## 6. Guess Number Estimation

**This section is the most relevant for the simulator use case.**

### 6.1 The Problem

Given a specific password, estimate how many guesses the PCFG generator would produce before reaching that password -- without actually running the generator to that point.

### 6.2 What the Grammar Gives You Directly

The PCFG grammar can compute the **probability** of any parseable password in O(1) time (after parsing):

```
P("Monkey69!") = P(base: L6_D2_S1) * P(L6: "monkey") * P(Cap6: "Ulllll") * P(D2: "69") * P(S1: "!")
```

If any component is missing from the grammar (e.g., an alpha string never seen in training), the probability is zero (or epsilon, depending on smoothing).

### 6.3 From Probability to Guess Number

The guess number G(p) for a password with probability p is:

```
G(p) = |{ password' : P(password') > P(p) }| + (rank within tied passwords)
```

Computing this exactly requires enumerating all passwords with higher probability, which is what the generator does. But there are faster approximation methods.

### 6.4 Approach 1: Precomputed Lookup Table (Recommended)

**Concept:** Run the PCFG generator once to a desired depth, recording (probability, cumulative_guess_number) pairs at regular intervals.

```python
# One-time precomputation
table = []  # List of (log_probability, guess_number) tuples
for i, (password, prob) in enumerate(pcfg_generator()):
    if i % 10000 == 0:  # Sample every 10K guesses
        table.append((math.log(prob), i))
    if i > MAX_GUESSES:
        break

# Runtime estimation
def estimate_guess_number(password):
    prob = compute_pcfg_probability(password)
    log_prob = math.log(prob)
    # Binary search in table for closest log_prob
    idx = bisect.bisect_left(table, (log_prob,))
    return interpolate(table, idx, log_prob)
```

**Pros:** O(1) per lookup after precomputation, simple to implement.
**Cons:** Accuracy degrades for passwords beyond the precomputed range; the one-time generation run can be slow (hours/days for 10^10+ guesses).

### 6.5 Approach 2: Monte Carlo Estimation (Dell'Amico & Filippone)

The 2015 CCS paper "Monte Carlo Strength Evaluation" proposed an elegant sampling approach:

1. Sample N random passwords from the grammar (straightforward -- just sample each production rule according to its probability)
2. For each sample, record its probability
3. Use the empirical CDF of sampled probabilities to estimate the number of passwords above any probability threshold
4. Apply importance sampling corrections for better accuracy in the tails

**Pros:** Works for any probability level without full enumeration; mathematically principled error bounds.
**Cons:** Requires careful implementation of the sampling and correction; accuracy depends on sample size.

### 6.6 Approach 3: Analytical Counting

For each base structure B, count how many terminal combinations produce a probability above the target:

```
For base structure B with segments T1, T2, ..., Tk:
  target_terminal_prob = P(target) / P(B)

  Count combinations where:
    P(T1[r1]) * P(T2[r2]) * ... * P(Tk[rk]) > target_terminal_prob
```

This is equivalent to counting lattice points in a log-probability space. For structures with few segments (k <= 3), this can be done with nested loops or dynamic programming. For structures with many segments, it becomes a variant of the knapsack counting problem.

**Dynamic programming approach:**
```
Working in log-probability space:
  log_target = log(target_terminal_prob)

  For each segment, sort terminal log-probabilities

  Use DP over segments:
    dp[i][j] = number of ways to achieve cumulative log-prob >= j
               using segments 1..i
```

**Pros:** Exact computation for simple structures; no precomputation needed.
**Cons:** Exponential in the number of segments for exact counting; DP discretization introduces error.

### 6.7 Recommendation for the Simulator

**Start with Approach 1 (Precomputed Lookup Table):**
1. Train a PCFG grammar on your target password distribution
2. Run the generator for as many guesses as feasible (10^8 to 10^10)
3. Record (log_prob, guess_number) at regular intervals
4. At runtime, parse each password, compute its PCFG probability, and interpolate

**Graduate to Approach 2 (Monte Carlo) if:**
- You need estimates beyond the precomputed range
- You need confidence intervals on the estimates
- You want to avoid the upfront generation cost

**Use Approach 3 (Analytical) if:**
- You need exact results for specific structures
- You're analyzing simple grammars (few base structures, short segments)

---

## 7. Performance Characteristics

### 7.1 Generation Speed

| Metric | Approximate Value | Notes |
|--------|-------------------|-------|
| Guess generation rate | 10K--100K guesses/sec | Pure Python, single-threaded |
| With hashcat piping | Limited by hashcat's intake | Typically hashcat is the bottleneck for slow hashes |
| Training time | Seconds to minutes | Depends on training set size |
| Grammar load time | < 1 second | Small grammar files |

The tool is explicitly designed as a **candidate generator**, not a hash cracker. It outputs plaintext guesses to stdout, which are piped to hashcat or John the Ripper for hash comparison:

```bash
python3 pcfg_guesser.py -r <ruleset> | hashcat -m <hash_type> <hashfile>
```

### 7.2 Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Grammar in memory | 10--100 MB | Depends on training data size |
| Priority queue (early) | < 1 MB | Few pre-terminals initially |
| Priority queue (deep) | 100 MB -- 1 GB+ | Grows with generation depth |
| Python overhead | ~50 MB | Interpreter baseline |

The priority queue is the primary memory concern for long-running generation. Each pre-terminal in the queue stores the base structure reference, rank indices array, probability, and last-incremented index. For grammars with many base structures, the queue can hold millions of entries during deep generation.

### 7.3 Scalability Considerations

- **Training set size:** Larger training sets produce better grammars but increase terminal vocabulary size, which increases memory and slows generation slightly
- **Grammar complexity:** More base structures = more initial queue entries = faster queue growth
- **Depth of generation:** Memory grows roughly logarithmically with guess number for well-behaved grammars, but can spike for grammars with many similar-probability structures
- **No parallelism:** The priority queue algorithm is inherently sequential (each pop determines the next guesses). Parallelism would require partitioning the probability space.

---

## 8. The Original Weir et al. Paper (IEEE S&P 2009)

### 8.1 Core Contribution

Weir, Aggarwal, de Medeiros, and Glodek introduced the idea of using a **probabilistic context-free grammar trained on real password data** to generate password guesses in optimal probability order. This was a paradigm shift from the rule-based approach of existing tools (John the Ripper's mangling rules, dictionary + append-digits, etc.).

### 8.2 Key Insights

1. **Passwords have exploitable structure.** Humans create passwords by combining recognizable components (words, numbers, symbols) in predictable patterns. A grammar captures this structure.

2. **Probability ordering matters.** Generating the most likely passwords first maximizes the cracking rate for any given guess budget. This is provably optimal under the grammar's probability model.

3. **Training data transfers across sites.** A grammar trained on leaked passwords from one site is effective against passwords from a different site, because humans use similar password-creation strategies everywhere (with some variation).

### 8.3 Experimental Results

The paper tested PCFG against John the Ripper on multiple real password datasets:

- **PCFG cracked 28--129% more passwords** than JtR's wordlist mode given the same number of guesses
- The advantage was most pronounced in the **10^6 to 10^9 guess range** -- very weak passwords (top 10^4) are caught by any method, and very strong passwords resist all methods
- **Cross-site training** (training on MySpace passwords, cracking LinkedIn passwords) showed reduced but still significant improvement over JtR
- The grammar naturally adapted to different password policies (e.g., sites requiring special characters produced grammars that reflected this)

### 8.4 Limitations Acknowledged

- **Independence assumption:** A context-FREE grammar assumes segments are independent. In reality, someone who chooses "love" might prefer "69" or "4ever" as a suffix more than a random person would. This correlation is lost.
- **Training data dependency:** The quality of the grammar is bounded by the representativeness of the training data.
- **No character-level modeling within segments:** The alpha segment "dragon" is stored as an atomic unit. The grammar doesn't learn that "dr" is a common letter bigram -- it just memorizes whole strings.

### 8.5 Impact

The paper has been cited over 700 times and spawned an entire subfield of probabilistic password modeling, including Markov models (OMEN), neural network approaches (FLA, PassGAN), and hybrid systems. The PCFG remains a gold-standard baseline in password security research.

---

## 9. LPG-PCFG and Subsequent Improvements

### 9.1 The Long Tail Problem

The standard PCFG has a known weakness: the probability distribution over passwords is extremely heavy-tailed. The top 10^6 guesses cover perhaps 10--30% of a typical password set, but reaching the next 10% requires 10--100x more guesses, each individually very low probability. The priority queue becomes increasingly expensive to maintain in this regime.

### 9.2 Matt Weir's Own Improvements (v4.x Python Rewrite)

The current pcfg_cracker incorporates several advances over the original 2009 version:

- **Keyboard walk detection:** Captures `qwerty`, `asdf`, and similar patterns as first-class tokens
- **Leet-speak handling:** Un-leets during training, re-applies during generation, dramatically improving coverage of leet variants
- **Context-sensitive tokens:** Years and dates are modeled with their own probability distributions rather than being treated as generic digit strings
- **Multi-word detection:** Identifies concatenated dictionary words, improving generalization for long alpha segments
- **Improved encoding support:** Better Unicode handling for international password sets
- **Prince-mode style combination:** Ability to combine words from the grammar in ways inspired by the PRINCE attack

### 9.3 LPG-PCFG (Low-Probability Guessing)

> **Uncertainty flag:** My knowledge of LPG-PCFG is less detailed than the core pcfg_cracker. The following is my best understanding.

LPG-PCFG (circa 2022) addresses the efficiency of generating low-probability guesses. Key ideas likely include:

- **Better smoothing models** for unseen terminals, allowing the grammar to assign non-zero probabilities to strings not in the training data
- **Alternative enumeration strategies** for the long tail, potentially abandoning strict probability ordering in favor of approximate ordering that's cheaper to maintain
- **Improved memory management** for deep generation runs where the priority queue would otherwise grow prohibitively

### 9.4 The Broader PCFG Lineage

| System | Year | Advance |
|--------|------|---------|
| Weir et al. PCFG | 2009 | Original grammar-based approach |
| OMEN (Markov) | 2015 | Character-level Markov model, faster enumeration |
| Houshmand & Aggarwal | 2017 | Semantic-aware PCFG extensions |
| FLA (neural) | 2016 | Recurrent neural network password model |
| PassGAN | 2019 | GAN-based password generation |
| pcfg_cracker v4.x | 2020+ | Keyboard walks, leet-speak, context tokens |
| LPG-PCFG | 2022 | Low-probability guess optimization |

---

## 10. Extractable Patterns for Our Simulator

This section directly addresses what we can extract from the PCFG grammar for analytical password strength estimation.

### 10.1 What the Grammar Files Provide

From a trained PCFG grammar (the `Rules/` directory), we can directly extract:

1. **Base structure distribution:** Every observed structure and its probability. This tells us how likely any given structural pattern is.

2. **Terminal distributions per type and length:** For every (type, length) pair, the complete probability distribution over observed values. These files are already sorted by probability.

3. **Capitalization mask distributions:** Per alpha-string length, the probability of each capitalization pattern.

4. **Keyboard walk patterns:** Common walks and their probabilities.

5. **Context-sensitive patterns:** Year distributions, date format distributions.

### 10.2 Computing P(password) Analytically

Given a password, compute its PCFG probability without running the generator:

```python
def pcfg_probability(password, grammar):
    """Compute the probability of a password under a PCFG grammar."""

    # Step 1: Parse into structure
    segments = parse_password(password)
    # e.g., [("L", "monkey"), ("D", "69"), ("S", "!")]

    structure = structure_string(segments)
    # e.g., "L6D2S1"

    # Step 2: Look up base structure probability
    p_structure = grammar.base_structures.get(structure, 0.0)
    if p_structure == 0:
        return 0.0  # Unknown structure

    # Step 3: Multiply terminal probabilities
    p_total = p_structure
    for seg_type, seg_value in segments:
        if seg_type == "L":
            lower_value = seg_value.lower()
            cap_mask = extract_cap_mask(seg_value)
            p_total *= grammar.alpha[len(seg_value)].get(lower_value, 0.0)
            p_total *= grammar.capitalization[len(seg_value)].get(cap_mask, 0.0)
        elif seg_type == "D":
            p_total *= grammar.digits[len(seg_value)].get(seg_value, 0.0)
        elif seg_type == "S":
            p_total *= grammar.special[len(seg_value)].get(seg_value, 0.0)
        elif seg_type == "K":
            p_total *= grammar.keyboard[len(seg_value)].get(seg_value, 0.0)

    return p_total
```

### 10.3 Converting Probability to Guess Number

**The precomputed lookup table approach (recommended for the simulator):**

```python
import bisect, math

class PCFGStrengthEstimator:
    def __init__(self, grammar, lookup_table):
        """
        grammar: Loaded PCFG grammar
        lookup_table: List of (log_prob, guess_number) tuples,
                      sorted by log_prob descending,
                      precomputed by running the generator once
        """
        self.grammar = grammar
        # Table of (log_prob, cumulative_guesses), sorted by log_prob descending
        self.log_probs = [entry[0] for entry in lookup_table]
        self.guess_nums = [entry[1] for entry in lookup_table]

    def estimate_guess_number(self, password):
        prob = pcfg_probability(password, self.grammar)
        if prob == 0:
            return float('inf')  # Not in grammar

        log_prob = math.log(prob)

        # Find position in lookup table
        idx = bisect.bisect_left(self.log_probs, log_prob)

        if idx == 0:
            return 1  # Higher probability than anything in table
        if idx >= len(self.log_probs):
            return self.guess_nums[-1]  # Beyond table range

        # Linear interpolation between adjacent table entries
        frac = ((log_prob - self.log_probs[idx-1]) /
                (self.log_probs[idx] - self.log_probs[idx-1]))
        estimated = (self.guess_nums[idx-1] +
                    frac * (self.guess_nums[idx] - self.guess_nums[idx-1]))

        return int(estimated)
```

### 10.4 Building the Lookup Table

```bash
# Generate guesses and record probability checkpoints
python3 pcfg_guesser.py -r MyGrammar --probability-output | \
  python3 build_lookup_table.py --sample-interval 10000 --max-guesses 1000000000
```

The generator would need to output probabilities alongside guesses (pcfg_cracker may support this with a flag, or you'd modify the guesser to print probabilities). You then sample at regular intervals to build the table.

### 10.5 What This Enables for the Simulator

With a trained PCFG grammar and a precomputed lookup table, the simulator can:

1. **Estimate password strength in O(1) per password** -- parse, compute probability, interpolate in table
2. **Classify passwords by structural weakness** -- the base structure alone tells you a lot (L8D2S1 is common; L3S2K5D4 is rare)
3. **Compare password policies** -- train grammars on passwords from different policies, compare the resulting strength distributions
4. **Model attacker knowledge** -- the grammar represents what an attacker trained on a specific leak would know; different training data produces different grammars and different strength estimates
5. **Provide interpretable feedback** -- "Your password has the structure LetterDigitSymbol, which accounts for X% of passwords; your specific digit suffix '123' is the most common 3-digit suffix" -- this comes directly from the grammar's probability tables

### 10.6 Limitations and Caveats

- **Coverage:** The PCFG assigns zero probability to passwords with unseen terminals (unless smoothing is applied). This is a significant fraction of real passwords -- perhaps 20--40% of a typical password set.
- **Independence assumption:** The grammar overestimates the probability of some combinations and underestimates others. "iloveyou69" might be more common than the grammar predicts from independent probabilities of "iloveyou" and "69".
- **Training data bias:** The grammar reflects the population that created the training data. Training on RockYou will produce different strength estimates than training on a corporate password set.
- **Lookup table resolution:** The precomputed table has finite resolution. For passwords near the boundary between sample points, the estimate can be off by a factor of 2--10x. This is usually acceptable for strength classification (weak/medium/strong) but not for precise ranking.

---

## References

1. Weir, M., Aggarwal, S., de Medeiros, B., & Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." *IEEE Symposium on Security and Privacy (S&P 2009)*.
2. Weir, M. (2010). "Using Probabilistic Techniques to Aid in Password Cracking Attacks." *PhD Dissertation, Florida State University*.
3. Dell'Amico, M. & Filippone, M. (2015). "Monte Carlo Strength Evaluation: Fast and Reliable Password Checking." *ACM CCS 2015*.
4. Kelley, P.G., et al. (2012). "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms." *IEEE S&P 2012*.
5. Ur, B., et al. (2015). "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." *USENIX Security 2015*.
6. Houshmand, S. & Aggarwal, S. (2017). "Building Better Passwords Using Probabilistic Techniques."
7. Matt Weir's pcfg_cracker repository: https://github.com/lakiw/pcfg_cracker

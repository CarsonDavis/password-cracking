# Technical Analysis: RUB-SysSec Password-Guessing-Framework and OMEN

**Date:** 2026-02-15
**Author:** Research analysis for password-cracking simulator project
**Repositories:**
- https://github.com/RUB-SysSec/Password-Guessing-Framework
- https://github.com/RUB-SysSec/OMEN

**Caveat:** Web search and fetch tools were unavailable during this research session. This analysis draws on knowledge of both repositories and their associated publications from training data. Specific details (exact file paths, line counts, last commit dates) should be verified against the live repositories before relying on them for implementation decisions.

---

## Executive Summary

The RUB-SysSec Password-Guessing-Framework is a Python-based orchestration harness that enables fair, standardized comparison of password guessing strategies. It does not implement guessing algorithms itself -- instead, it wraps external tools (OMEN, PCFG Cracker, John the Ripper, Hashcat, neural models) in a common pipeline of train-generate-evaluate-compare. Its primary output is **guessability curves**: plots of guess number vs. percentage of a test set cracked, the standard metric in password security research.

OMEN (Ordered Markov ENumerator) is a standalone C tool from the same research group that uses character-level n-gram models to generate password guesses in approximate probability order. Its key innovation is **level-based enumeration**, which discretizes password probabilities into integer levels and enumerates all passwords at each level before moving to the next. This solves the hard problem of generating Markov-model candidates in probability order without maintaining an exponentially large priority queue.

For our simulator, the most valuable design patterns from these tools are: (1) the separation of guessing strategy from evaluation harness, (2) the use of guess-number curves as the universal comparison metric, (3) OMEN's level-based enumeration as an efficient approximation to exact probability ordering, and (4) the configuration-driven experiment design that enables reproducibility.

---

## Table of Contents

1. [Password-Guessing-Framework: Architecture and Design](#1-password-guessing-framework-architecture-and-design)
2. [Supported Guessing Strategies](#2-supported-guessing-strategies)
3. [Input/Output Formats](#3-inputoutput-formats)
4. [Benchmarking Methodology and Metrics](#4-benchmarking-methodology-and-metrics)
5. [OMEN Deep Dive: Ordered Markov Enumeration](#5-omen-deep-dive-ordered-markov-enumeration)
6. [Associated Academic Papers](#6-associated-academic-papers)
7. [Code Quality and Maintainability](#7-code-quality-and-maintainability)
8. [Lessons for Our Simulator](#8-lessons-for-our-simulator)

---

## 1. Password-Guessing-Framework: Architecture and Design

### Repository Structure

The framework is organized around a central Python orchestrator with subdirectories for each supported guessing strategy:

```
Password-Guessing-Framework/
├── README.md
├── framework/
│   ├── __init__.py
│   ├── config.py           # Configuration management (INI/YAML parsing)
│   ├── manager.py          # Main orchestration: train -> generate -> evaluate
│   ├── selector.py         # Strategy selection and instantiation
│   ├── evaluator.py        # Crack-rate computation and comparison
│   └── utils/              # Shared utilities
├── guesser/
│   ├── pcfg/               # Wrapper for Weir's PCFG Cracker
│   ├── omen/               # Wrapper for OMEN (createNG/enumNG)
│   ├── john/               # Wrapper for John the Ripper
│   ├── hashcat/            # Wrapper for Hashcat (--stdout mode)
│   └── neural/             # Wrapper for neural network guessers
├── data/                   # Training and test password lists
├── results/                # Output directory for experiment results
├── scripts/                # Shell scripts for setup and batch runs
├── requirements.txt        # Python dependencies
└── config files            # Experiment configuration
```

### Languages and Dependencies

| Component | Language | Notes |
|-----------|----------|-------|
| Framework core | Python 3.6+ | Orchestration, evaluation, plotting |
| OMEN | C | Compiled separately; invoked via subprocess |
| PCFG Cracker | Python/Java (Weir's implementation) | External dependency |
| John the Ripper | C | System install or compiled from source |
| Hashcat | C/OpenCL | System install |
| Neural models | Python (TensorFlow/PyTorch) | Depends on which model is used |
| Plotting | Python (matplotlib) | Guessability curve visualization |
| Shell scripts | Bash | Setup, batch orchestration |

### Mechanistic Workflow

The framework operates as a five-phase pipeline:

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CONFIGURE   │───>│    TRAIN      │───>│   GENERATE   │───>│   EVALUATE   │───>│   COMPARE    │
│             │    │              │    │              │    │              │    │              │
│ - Strategies│    │ - Each model │    │ - Candidates │    │ - Match vs   │    │ - Plot curves│
│ - Data paths│    │   trained on │    │   generated  │    │   test set   │    │ - Tables     │
│ - Budget    │    │   same data  │    │   up to      │    │ - Count      │    │ - Summary    │
│ - Params    │    │              │    │   budget     │    │   cumulative │    │   statistics │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

The critical design decision is that **the framework does not reimplement any guessing algorithm**. Each strategy is an external tool invoked through subprocess calls. The framework's value is in standardizing the training data, evaluation methodology, and comparison visualization so that results are directly comparable.

### Key Data Structures

- **Manager/Orchestrator:** Central class that drives the pipeline. Holds references to all configured guesser wrappers and the evaluator.
- **Guesser wrappers:** Each follows a common interface pattern with `train(training_set_path)` and `generate(output_path, budget)` methods. Internally, each wrapper constructs command-line invocations for the external tool.
- **Evaluator:** Loads the test set into a Python `set` for O(1) membership testing. Streams through each guesser's candidate file, tracking the cumulative crack count at each guess number.
- **Results containers:** Dictionaries or dataframes mapping `{strategy_name -> [(guess_number, cumulative_cracks), ...]}`.

---

## 2. Supported Guessing Strategies

### 2.1 PCFG (Probabilistic Context-Free Grammar)

Based on Weir et al. (CCS 2010). The PCFG approach models passwords as sequences of character-class segments:

- **Structure learning:** Decomposes training passwords into patterns like `L4D3S1` (4 lowercase letters, 3 digits, 1 symbol)
- **Terminal distributions:** For each character class and length, learns the frequency distribution of actual values (e.g., "pass" appears with probability 0.02 in the L4 class)
- **Probability-ordered generation:** Uses a priority queue (min-heap on negative log-probability) to generate the next most probable password without enumerating all possibilities
- **Strength:** Captures high-level structural patterns that humans use; excellent at guessing passwords that follow common templates

### 2.2 OMEN (Ordered Markov Enumerator)

Based on Duermuth et al. (ESSoS 2015). Character-level Markov model with level-based enumeration. (See Section 5 for detailed analysis.)

### 2.3 John the Ripper

The framework wraps JtR in two modes:
- **Wordlist + rules:** A base dictionary with mangling rules (capitalize, append digits, leet-speak substitutions, etc.)
- **Incremental mode:** Character-by-character brute force guided by Markov-like frequency tables
- **Capture method:** JtR is typically run in `--stdout` mode to emit candidates without needing actual hashes

### 2.4 Hashcat

Used in `--stdout` mode (candidate generation without hash cracking):
- **Rule-based transformations:** Applies rule files to a base wordlist (toggle case, insert characters, reverse, etc.)
- **Combinator attacks:** Concatenates words from two dictionaries
- **Mask attacks:** Brute force within a character-class template (e.g., `?u?l?l?l?d?d?d?d`)
- **Strength:** Extremely fast; rule files encode real-world password creation patterns

### 2.5 Neural Network Models

Based on Melicher et al. (USENIX Security 2016) and similar work:
- **Architecture:** Character-level RNN or LSTM trained on password data
- **Generation:** Either sampling (for fast but unordered generation) or enumeration (for probability-ordered generation via beam search or Monte Carlo methods)
- **Guess number estimation:** The model can estimate a password's guess number without explicit enumeration, by computing the password's probability and mapping it to an approximate rank
- **Strength:** Captures subtle character-level patterns that grammar-based models miss; can model long-range dependencies

### 2.6 PassGAN (Generative Adversarial Network)

Based on Hitaj et al. (ACNS 2019):
- **Architecture:** GAN with a generator that produces password-length character sequences and a discriminator that distinguishes real from generated passwords
- **Generation:** Sampling from the generator (no natural probability ordering)
- **Limitation:** Cannot produce probability-ordered candidates; difficult to estimate guess numbers

### 2.7 Dictionary Baselines

Simple wordlist attacks used as baselines:
- Raw frequency-sorted wordlists (no transformations)
- Useful for establishing a lower bound on guessing effectiveness

### Strategy Comparison Summary

| Strategy | Probability Ordering | Guess Number Estimation | Training Speed | Generation Speed | Model Type |
|----------|---------------------|------------------------|----------------|-----------------|------------|
| PCFG | Exact | Yes (via priority queue position) | Minutes | Fast | Structured |
| OMEN | Approximate (levels) | Approximate (level-based) | Seconds | Very fast (C) | Statistical |
| JtR Rules | No (rule order) | No | N/A (rule files) | Fast | Heuristic |
| Hashcat | No (rule order) | No | N/A (rule files) | Very fast (GPU) | Heuristic |
| Neural | Approximate (sampling/beam) | Yes (probability-based) | Hours (GPU) | Moderate | Learned |
| PassGAN | No | No | Hours (GPU) | Moderate | Learned |
| Dictionary | Frequency order | By rank in list | N/A | I/O bound | Lookup |

---

## 3. Input/Output Formats

### Inputs

**Training password list:** A plaintext file, one password per line, newline-delimited. Typically millions of passwords from leaked datasets (RockYou is the canonical example, though ethical research may use synthetic or sanitized data).

```
password123
iloveyou
12345678
qwerty
letmein
...
```

**Test password list:** Same format. Must be disjoint from the training set to avoid information leakage. The framework may handle the train/test split, or it may expect pre-split files.

**Configuration file:** INI-style or similar, specifying:
```ini
[experiment]
name = rockyou_comparison
budget = 1000000000

[data]
training_set = data/rockyou_train.txt
test_set = data/rockyou_test.txt

[guessers]
pcfg = true
omen = true
john = true
neural = false

[omen]
ngram_order = 4
smoothing = additive
path = /usr/local/bin/omen

[pcfg]
path = /opt/pcfg_cracker/
...
```

### Outputs

**Candidate files:** One file per strategy, one candidate per line, in generation order:
```
password
123456
password1
abc123
...
```

**Evaluation data:** CSV or tabular format:
```csv
guess_number,pcfg_cracked,omen_cracked,john_cracked
1000,1523,1201,1089
10000,4521,3987,3456
100000,12034,11456,10234
1000000,28456,27890,25678
...
```

**Guessability curves:** PNG/PDF plots with:
- X-axis: Guess number (log scale, typically 10^0 to 10^14)
- Y-axis: Percentage of test set cracked (0-100%)
- One line per strategy
- These are the standard visualization in password security papers

---

## 4. Benchmarking Methodology and Metrics

### Primary Metric: Guessability Curves

The guessability curve plots the cumulative fraction of a test set that has been cracked as a function of the number of guesses attempted. This is the gold standard metric in the field, established by Ur et al. (USENIX Security 2015).

The curve captures the essential tradeoff: given a fixed computational budget (number of guesses an attacker can make), which strategy cracks the most passwords?

```
100% ─────────────────────────────────────
 90% ─                          ___-------
 80% ─                     __--/
 70% ─                  _-/
 60% ─               _-/ .....PCFG
 50% ─            _-/ ...
 40% ─          _/...       ----OMEN
 30% ─       _/.            ....Neural
 20% ─    __/
 10% ─  _/
  0% ─/─────────────────────────────────
      10^0  10^3  10^6  10^9  10^12  10^14
                  Guess Number
```

### Secondary Metrics

1. **Crack rate at fixed thresholds:** "At 10^6 guesses, PCFG cracks 34.2%, OMEN cracks 31.8%, JtR cracks 29.1%." This provides discrete comparison points.

2. **Complementarity analysis:** How many passwords does strategy A crack that strategy B does not, and vice versa? High complementarity suggests combining strategies would be beneficial.

3. **Coverage ceiling:** The maximum fraction of the test set that a strategy could ever crack, even with unlimited guesses. Some passwords (very long, very random) may be outside any model's effective reach.

4. **Guess number for individual passwords:** Given a specific password, what is its rank in each strategy's ordering? This enables per-password strength estimation.

### Ensuring Fair Comparison

The framework enforces several invariants:
- **Identical training data** for all strategies
- **Identical test data** for evaluation
- **Identical guess budget** (or at minimum, comparison at the same budget points)
- **Unique-candidate counting:** Duplicate guesses within a strategy's output are counted only once
- **No information leakage:** Test set is strictly withheld from training

These invariants are deceptively important. Without them, comparisons are meaningless -- a strategy trained on more data or evaluated against a weaker test set will appear artificially better.

---

## 5. OMEN Deep Dive: Ordered Markov Enumeration

### The Enumeration Problem

The core challenge OMEN solves: Markov models assign probabilities to strings, but generating strings in probability order is computationally hard. A naive approach would maintain a priority queue of all partial strings, which grows exponentially. OMEN's insight is that **exact ordering is unnecessary** -- approximate ordering via discretized probability levels is sufficient for practical password guessing.

### Architecture

OMEN consists of two main programs, both written in C:

**`createNG` (Training)**
- Reads a password file
- Builds four data structures:
  1. **IP (Initial Probability) table:** For each possible starting n-gram (first n characters), stores its frequency count across the training set
  2. **CP (Conditional Probability) table:** For each (n-1)-gram context, stores the frequency of each following character
  3. **EP (End Probability) table:** For each (n-1)-gram context, stores the frequency of the password ending at that point
  4. **LN (Length) table:** Frequency distribution of password lengths in the training set
- Applies smoothing (additive/Laplace) to all tables
- Quantizes probabilities into integer levels (typically 0-10 or similar range)
- Writes tables to binary files on disk

**`enumNG` (Enumeration)**
- Loads the pre-computed tables
- Enumerates passwords level by level, starting from level 0 (highest probability)
- For each level and each password length:
  - Finds all combinations of IP, CP transitions, and EP whose quantized levels sum to the target level
  - Systematically generates all such passwords
- Outputs candidates to stdout or a file

### The Level System

The level system is the key innovation. Instead of maintaining exact probabilities (which would require arbitrary-precision arithmetic and exponentially large priority queues), OMEN discretizes:

```
Exact probability: 0.0000234  -->  Level 3
Exact probability: 0.0000198  -->  Level 3
Exact probability: 0.0000012  -->  Level 5
Exact probability: 0.0000001  -->  Level 7
```

The discretization works by taking the log-probability and dividing it into bins. The total level of a password is the sum of the levels of its component n-grams:

```
Level(password) = Level(IP) + Level(CP_1) + Level(CP_2) + ... + Level(EP)
```

This transforms the problem from "enumerate strings in exact probability order" to "enumerate strings whose component levels sum to a target value" -- a constrained combinatorial problem that can be solved efficiently through systematic enumeration.

### N-gram Model Details

For a password `p = c_1 c_2 c_3 ... c_m` with n-gram order `n`:

```
P(p) = P_IP(c_1...c_n) * P_CP(c_{n+1} | c_2...c_n) * P_CP(c_{n+2} | c_3...c_{n+1}) * ... * P_EP(end | c_{m-n+2}...c_m) * P_LN(m)
```

Where:
- `P_IP` is the initial probability of the first n-gram
- `P_CP` are conditional probabilities for each subsequent character
- `P_EP` is the probability of ending after the final (n-1)-gram
- `P_LN` is the probability of the password having length m

### Smoothing

OMEN uses **additive (Laplace) smoothing** to handle the zero-frequency problem:

```
P_smoothed(c | context) = (count(context, c) + delta) / (count(context) + delta * |alphabet|)
```

Where `delta` is a small constant (configurable, often 1 or a fraction thereof). This ensures:
- Every character transition has nonzero probability
- The model can generate any string over the alphabet
- Rare but valid passwords are not assigned zero probability

The smoothing parameter significantly affects performance:
- **Too little smoothing:** Model cannot generate passwords containing unseen n-grams; misses rare but real passwords
- **Too much smoothing:** Model approaches uniform distribution; loses discriminative power; generates too many nonsensical candidates early

### Estimating Guess Numbers for Arbitrary Passwords

OMEN can estimate the guess number for a given password through its `evalPW` functionality:

1. **Compute the password's level:** Apply the trained model to compute the probability of each n-gram transition, quantize each to a level, and sum them. This gives the password's overall level.

2. **Estimate the guess number:**
   - Count the total number of passwords at all levels below the password's level (these would all be guessed first)
   - Add an estimate of the password's position within its own level
   - The result is an approximate guess number

3. **Accuracy characteristics:**
   - The estimate is exact in terms of which passwords come before vs. after (at the level granularity)
   - Within a level, the position is approximate
   - For common passwords (low levels), the estimate is quite accurate because each level contains relatively few passwords
   - For rare passwords (high levels), the estimate becomes very rough because each level may contain billions or trillions of candidates
   - The approximation is generally within 1-2 orders of magnitude of the true guess number

4. **Use case for our simulator:** We could use OMEN's level system to quickly estimate password strength without full enumeration. A password at level 2 is much weaker than one at level 8, regardless of exact guess numbers.

### Performance Characteristics

| Metric | Typical Value |
|--------|--------------|
| Training time | Seconds to low minutes (millions of passwords) |
| Enumeration rate | Millions of candidates/second |
| Memory footprint | Tens of MB (depends on n-gram order, alphabet size) |
| Disk storage (tables) | Small (< 100 MB typically) |
| N-gram order | 3-4 (higher = more context, more storage) |
| Alphabet size | ~95 (printable ASCII) |

---

## 6. Associated Academic Papers

### Primary Papers

**1. OMEN: Faster Password Guessing Using an Ordered Markov Enumerator**
- Authors: Markus Duermuth, Fabian Angelstorf, Claude Castelluccia, Adrienne Felt Perito, Abdelberi Chaabane
- Venue: ESSoS 2015 (International Symposium on Engineering Secure Software and Systems)
- Key contributions:
  - Introduces level-based enumeration for Markov models
  - Demonstrates that approximate probability ordering is sufficient for effective password guessing
  - Shows OMEN is competitive with PCFG while being simpler and faster to train
  - Provides the theoretical framework for discretized probability enumeration

**2. Measuring Real-World Accuracies and Biases in Modeling Password Guessability**
- Authors: Blase Ur, Sean M. Segreti, Lujo Bauer, Nicolas Christin, Lorrie Faith Cranor, Saranga Komanduri, Darya Kurilova, Michelle L. Mazurek, William Melicher, Richard Shay
- Venue: USENIX Security 2015
- Key contributions:
  - Comprehensive methodology for comparing password guessing strategies
  - Shows that different strategies have complementary strengths (no single best approach)
  - Demonstrates that guessability estimates vary significantly across tools, highlighting the need for standardized comparison
  - Directly motivates the Password-Guessing-Framework's existence

**3. Testing Metrics for Password Creation Policies by Attacking Large Sets of Revealed Passwords**
- Authors: Matt Weir, Sudhir Aggarwal, Breno de Medeiros, Bill Collins
- Venue: ACM CCS 2010
- Key contributions:
  - Introduces the PCFG model for password guessing
  - Demonstrates probability-ordered generation via priority queue
  - Foundational work that most subsequent password guessing research builds upon

**4. Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks**
- Authors: William Melicher, Blase Ur, Sean M. Segreti, Saranga Komanduri, Lujo Bauer, Nicolas Christin, Lorrie Faith Cranor
- Venue: USENIX Security 2016
- Key contributions:
  - First practical neural network approach to password guessing
  - Shows RNNs can match or exceed PCFG and Markov models
  - Introduces Monte Carlo method for estimating guess numbers from a neural model without full enumeration
  - Demonstrates client-side password strength estimation using a compressed neural model

### Related Papers from the Same Group

**5. On Password Guessing with GPUs and FPGAs**
- Authors: Markus Duermuth, Thorsten Kranz
- Venue: PASSWORDS 2014
- Relevance: Hardware-acceleration context; understanding the scale at which guessing operates in practice

**6. PassGAN: A Deep Learning Approach for Password Guessing**
- Authors: Briland Hitaj, Paolo Gasti, Giuseppe Ateniese
- Venue: ACNS 2019
- Relevance: Alternative neural approach (GAN-based) that the framework may support

---

## 7. Code Quality and Maintainability

### Strengths

- **Clear separation of concerns:** The framework cleanly separates orchestration from guessing strategy implementation. Each guesser is an independent module with a consistent interface.
- **Configuration-driven:** Experiments are defined by config files, supporting reproducibility.
- **Standard evaluation methodology:** Implements the accepted academic methodology for guessability comparison.
- **Extensible design:** New guessing strategies can be added by creating a new wrapper module.

### Weaknesses

- **Research-grade code:** This is academic software, not production code. Error handling is minimal, edge cases may not be covered, and there are likely few or no automated tests.
- **Documentation gaps:** The README provides basic usage instructions, but detailed API documentation is sparse. Understanding the code requires reading the source alongside the papers.
- **Subprocess-heavy architecture:** Reliance on subprocess calls for external tools introduces fragility (path dependencies, output format assumptions, version compatibility issues).
- **Maintenance status:** The repository appears to have been last actively maintained around 2019-2020. Academic code often has a limited maintenance window tied to the associated paper/thesis.
- **Limited error reporting:** When an external tool fails, debugging can be difficult because the framework may not surface the underlying error clearly.

### OMEN Code Quality (C codebase)

- Well-structured for a C project of its size
- Clear separation between training (`createNG`) and enumeration (`enumNG`)
- Binary file formats for n-gram tables are efficient but not self-documenting
- Configurable through a text-based config file
- Last actively maintained around 2017-2018

---

## 8. Lessons for Our Simulator

### Design Patterns to Adopt

**1. Strategy/Plugin Architecture**
The framework's separation of the orchestration harness from individual guessing strategies is the right pattern. Our simulator should define a clean interface for attack strategies and allow new ones to be plugged in without modifying the core.

```python
class GuessingStrategy(ABC):
    @abstractmethod
    def train(self, training_data: Path) -> None: ...

    @abstractmethod
    def generate(self, budget: int) -> Iterator[str]: ...

    @abstractmethod
    def estimate_guess_number(self, password: str) -> Optional[int]: ...
```

**2. Guessability Curves as the Universal Metric**
Adopt guess-number vs. crack-rate curves as our primary comparison metric. This is the accepted standard in the field and enables direct comparison with published results.

**3. Configuration-Driven Experiments**
All experiment parameters should be in config files, not hardcoded. This enables reproducibility and systematic parameter sweeps.

**4. Level-Based Probability Discretization (from OMEN)**
For our Markov model implementation, OMEN's level system is an elegant solution to the enumeration problem. We should adopt this approach rather than attempting exact probability ordering, which is computationally intractable at scale.

**5. Set-Based Evaluation**
The pattern of loading the test set into a hash set for O(1) lookup during evaluation is simple and correct. We should do the same.

### Design Patterns to Avoid or Improve Upon

**1. Subprocess-Based Integration**
The framework's reliance on subprocess calls makes it fragile and hard to debug. For our simulator, we should prefer native Python implementations or well-defined library interfaces over shelling out to external binaries. Where external tools are necessary, wrap them with robust error handling and output parsing.

**2. Minimal Testing**
Academic code's lack of tests is understandable given its context but should not be replicated. Our simulator should have unit tests for core algorithms (n-gram computation, level assignment, PCFG parsing) and integration tests for the pipeline.

**3. Sparse Documentation**
We should document not just how to use the code but why specific design decisions were made. The algorithmic rationale (which currently lives only in papers) should be captured in code comments and design docs.

**4. Binary File Formats Without Versioning**
OMEN's binary n-gram tables are efficient but not self-describing. Our model storage should include version metadata and be inspectable (JSON/MessagePack with a schema, or HDF5).

**5. Monolithic Evaluation**
The framework evaluates after all candidates are generated. For large-scale experiments, streaming evaluation (checking candidates as they're generated) would reduce memory usage and enable early stopping.

### Specific Technical Takeaways

**For our Markov model:**
- Use OMEN's 4-component probability model (IP + CP + EP + LN)
- Implement level-based enumeration for ordered generation
- Use additive smoothing with a tunable parameter
- Default to n-gram order 3 or 4; make it configurable
- Pre-compute level counts for fast guess-number estimation

**For our PCFG model:**
- Use Weir's decomposition into character-class segments
- Implement priority-queue-based enumeration for exact probability ordering
- Consider hybrid approaches that combine PCFG structure with Markov terminal generation

**For benchmarking:**
- Always compare against at least two baselines (one trivial like frequency-sorted dictionary, one strong like PCFG or neural)
- Report results at standard budget thresholds (10^6, 10^9, 10^12, 10^14)
- Measure and report complementarity between strategies
- Use the same train/test methodology as the RUB framework to enable comparison with published results

**For guess-number estimation:**
- OMEN's level-based approach is good for fast, approximate estimation
- For more precise estimation, consider the Monte Carlo method from Melicher et al. (2016)
- Both approaches have tradeoffs: level-based is fast but coarse; Monte Carlo is more precise but slower
- For a password strength meter (real-time feedback), level-based estimation is likely sufficient

---

## Appendix: Quick Reference

### Running OMEN (from the OMEN repository)

```bash
# Training: build n-gram tables from a password list
./createNG --iPwdList training_passwords.txt

# Enumeration: generate candidates
./enumNG --simulated 1000000    # generate up to 1M candidates

# Evaluation: estimate a password's guess number
./evalPW
> password123
> Level: 2, Approximate guess number: 4521
```

### Key Configuration Parameters (OMEN)

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `ngramsize` | Order of the n-gram model | 4 |
| `alphabet` | Character set | printable ASCII (~95 chars) |
| `maxlength` | Maximum password length to consider | 20-30 |
| `smoothing` | Smoothing method | additive |
| `delta` | Smoothing constant | 1.0 |
| `maxlevel` | Maximum enumeration level | 10-20 |

### Key Equations

**OMEN password probability:**
```
log P(c_1...c_m) = log P_IP(c_1...c_n)
                 + sum_{i=n+1}^{m} log P_CP(c_i | c_{i-n+1}...c_{i-1})
                 + log P_EP(end | c_{m-n+2}...c_m)
                 + log P_LN(m)
```

**Level computation:**
```
Level(c_1...c_m) = L_IP(c_1...c_n)
                 + sum_{i=n+1}^{m} L_CP(c_i | c_{i-n+1}...c_{i-1})
                 + L_EP(end | c_{m-n+2}...c_m)
```
where `L_X(.) = floor(-log(P_X(.)) / bin_width)`

**Approximate guess number:**
```
GuessNumber(pw) ≈ sum_{level=0}^{Level(pw)-1} Count(level) + position_within_level
```

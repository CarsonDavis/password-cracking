# Research Background: CMU Guess Calculator Framework

**Date:** 2026-02-15
**Topic:** Technical analysis of CMU CUPS Lab's guess-calculator-framework and related tools

## Description

Deep technical study of the Carnegie Mellon CUPS Lab guess-calculator-framework, including repository structure, algorithms, cracking strategies simulated, input/output formats, relationship to other CMU tools (password_meter, neural_network_cracking), and associated academic papers. Goal is to extract design patterns relevant to building our own password cracking simulator.

## Methodology Note

Web search and web fetch tools were unavailable during this research session. Analysis is based on direct knowledge of these repositories and their associated academic publications from training data. All three repositories are public and can be cloned for verification:
- `git clone https://github.com/cupslab/guess-calculator-framework.git`
- `git clone https://github.com/cupslab/neural_network_cracking.git`
- `git clone https://github.com/cupslab/password_meter.git`

Findings should be verified against the actual repository contents.

## Sources

[1]: https://github.com/cupslab/guess-calculator-framework "guess-calculator-framework GitHub repo"
[2]: https://github.com/cupslab/neural_network_cracking "neural_network_cracking GitHub repo"
[3]: https://github.com/cupslab/password_meter "password_meter GitHub repo"
[4]: https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/ur "Ur et al., USENIX Security 2015"
[5]: https://ieeexplore.ieee.org/document/6234434 "Kelley et al., IEEE S&P 2012"
[6]: https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/melicher "Melicher et al., USENIX Security 2016"
[7]: https://dl.acm.org/doi/10.1145/2976749.2978332 "Ur et al., CCS 2016 - Design and Evaluation of a Data-Driven Password Meter"
[8]: https://www.ece.cmu.edu/~lbauer/ "Lujo Bauer CMU page"
[9]: https://www.cylab.cmu.edu/ "CMU CyLab"
[10]: https://cups.cs.cmu.edu/ "CMU CUPS Lab"

## Research Log

---

### Analysis: guess-calculator-framework repository structure

**Language:** Python (primarily Python 2.7 era, some Python 3 compatibility)

**Key files and directories (from training knowledge of the repo):**

- **`pwd_guess.py`** -- The main module. Contains the core logic for running password guessing calculations. This is the heart of the framework.
- **`pwd_guess_unit.py`** -- Unit tests for the main module.
- **`guess_calculator.py`** or similar entry point scripts for running calculations.
- **Configuration files** -- JSON-based config files specifying parameters for different guessing strategies.
- **`README.md`** -- Documentation describing setup and usage.
- **Training data directories** -- For storing password lists used to train models.
- **Requirements/setup files** -- `requirements.txt` or `setup.py` for Python dependencies.

**Dependencies (known):**
- Python standard library
- NumPy for numerical operations
- Potentially scikit-learn or similar ML libraries depending on the guessing strategy
- For neural network components: TensorFlow or Keras (but these may be in the separate neural_network_cracking repo)

**Last significant activity:** The repository has not seen major updates in several years (likely last substantive commits around 2016-2018 timeframe, corresponding to the publication cycle of associated papers).

---

### Analysis: What is a "guess calculator"?

A **guess calculator** (also called a "guess number calculator") is a tool that, given a password, estimates how many guesses it would take a particular cracking strategy to reach that password. This is distinct from:

1. **Actually running a cracker** (which would require generating all guesses up to the target)
2. **Simple entropy estimation** (which just computes theoretical bits of randomness)

The guess calculator approach is more nuanced: it models specific, realistic attack strategies and computes the rank (guess number) of a given password under each strategy. A password with guess number 1,000 is cracked in the first 1,000 attempts; one with guess number 10^15 is essentially uncrackable under that strategy.

**Why this matters:** Guess numbers provide a concrete, strategy-specific measure of password strength. Two passwords might have identical Shannon entropy but wildly different guess numbers under a Markov model attack, because one follows common patterns the attacker's model captures.

This concept was formalized in the "Guess Again" paper (Kelley et al., IEEE S&P 2012) ([5]) and refined in the "Measuring Real-World Accuracies and Biases" paper (Ur et al., USENIX Security 2015) ([4]).

---

### Analysis: Cracking strategies modeled

The guess-calculator-framework models several distinct password cracking strategies:

1. **Hashcat/John the Ripper rule-based attacks**: Simulates mangling rules applied to dictionary words. Takes a wordlist and a set of transformation rules (append digits, capitalize, leet-speak substitutions, etc.) and computes the order in which candidate passwords would be generated.

2. **Probabilistic context-free grammar (PCFG) attacks**: Based on Weir et al.'s work. Decomposes passwords into structural templates (e.g., L5D2S1 = 5 letters + 2 digits + 1 symbol) and assigns probabilities to each component. Generates guesses in probability-ranked order.

3. **Markov model attacks**: Uses character-level n-gram models trained on leaked password data. Generates passwords in order of decreasing probability according to the Markov chain.

4. **Mangling rules with dictionaries**: Models attackers who apply systematic transformations to dictionary words -- this is the most common real-world attack pattern.

5. **Brute force**: As a baseline, models exhaustive character-space enumeration.

The framework's key contribution is that it can run **all of these strategies against the same password set** and produce comparative guess-number curves, showing which strategy cracks which passwords fastest.

---

### Analysis: Input/output format

**Input:**
- A file of passwords to evaluate (typically one password per line, may include frequency counts)
- Configuration specifying which guessing strategy to use and its parameters
- Training data (leaked password lists) for training the probabilistic models
- For rule-based attacks: the specific rule files (e.g., Hashcat `.rule` files)

**Output:**
- For each password: the estimated guess number under the specified strategy
- Aggregate statistics: percentage of passwords cracked at various guess thresholds (e.g., 10^6, 10^9, 10^12 guesses)
- Data suitable for plotting guess-number CDF curves (the "guessability curve" -- x-axis is number of guesses, y-axis is fraction of passwords cracked)

The canonical output visualization is the **guess-number CDF curve**, which appears in virtually every paper from this group.

---

### Analysis: Core algorithms -- how guess numbers are computed

The framework uses **two fundamentally different approaches** depending on the strategy:

**Approach 1: Explicit enumeration (for rule-based and dictionary attacks)**

For deterministic strategies like Hashcat rules applied to a dictionary, the guess order is fully determined. The framework:
1. Takes the wordlist + rules
2. Computes the complete guess order (or a sufficient prefix)
3. Looks up each target password's position in that order
4. That position IS the guess number

This is tractable because rule-based attacks produce a finite (if large) set of candidates, and the order is deterministic.

**Approach 2: Analytical/probabilistic estimation (for PCFG and Markov models)**

For probabilistic strategies, explicitly enumerating all guesses up to 10^15 is infeasible. Instead:
1. The model assigns a probability to each password
2. The guess number is estimated as the count of passwords with probability >= the target password's probability
3. This can be computed analytically or via sampling

For PCFG: the probability decomposition allows direct computation. A password's probability is the product of its template probability and its component probabilities. The guess number is the number of passwords with equal or higher combined probability.

For Markov models: similar probability-ranking approach, but the computation is more complex due to the sequential nature of the model.

**Approach 3: Monte Carlo estimation (primarily in neural_network_cracking repo)**

The neural network approach (Melicher et al., USENIX Security 2016) uses Monte Carlo simulation to estimate guess numbers, since the neural network's probability space is too complex for analytical enumeration. This is described in detail in the neural_network_cracking analysis below.

---

### Analysis: neural_network_cracking repository

**Language:** Python, using TensorFlow/Keras

**Core concept:** Train a recurrent neural network (LSTM) on password data to learn the probability distribution over passwords. Then use the trained model to either:
1. **Generate** password guesses in approximate probability order
2. **Estimate** the guess number of a given password

**The Monte Carlo guess-number estimation method:**

This is the key algorithmic innovation from Melicher et al. ([6]). The problem: given a neural network that assigns probability p to a password, how do you estimate the password's guess number (i.e., how many passwords have probability >= p)?

The Monte Carlo approach:
1. **Sample** a large number of passwords from the neural network's distribution
2. For each sample, compute its probability under the model
3. **Count** how many sampled passwords have probability >= the target password's probability
4. **Scale** this count by the ratio of the total password space to the sample size

More precisely, the guess number G(pw) for a password pw with probability p(pw) is:

```
G(pw) = |{pw' : p(pw') >= p(pw)}|
```

This is estimated by:
```
G_hat(pw) = (N_total / N_sample) * |{pw'_i in sample : p(pw'_i) >= p(pw)}|
```

Where N_total is an estimate of the effective password space size.

In practice, the implementation:
1. Pre-generates a large sample (millions of passwords) from the RNN
2. Computes the probability of each sampled password
3. Sorts these probabilities to create an empirical CDF
4. For a new password, computes its probability and does a binary search into the sorted list to estimate its rank

**Key files in neural_network_cracking:**
- **`pwd_guess.py`** -- Main module (shared naming convention with guess-calculator-framework)
- **`train.py`** or similar -- Training script for the neural network
- **`enumerate.py`** or similar -- Enumeration/generation script
- **`guess_calculator.py`** -- Guess number calculation using Monte Carlo
- **`config.py`** or JSON configs -- Configuration management
- **Model files** -- Saved Keras/TF models

**Architecture:** Character-level LSTM that predicts the next character given the preceding characters. This naturally produces a probability distribution over all possible strings.

---

### Analysis: password_meter repository

**Language:** TypeScript/JavaScript (runs in the browser)

**Purpose:** A client-side password strength meter that provides real-time feedback to users as they create passwords. This is the **user-facing** tool, as opposed to the research-oriented guess-calculator-framework.

**Relationship to guess-calculator-framework:**
- The password_meter uses a **compressed neural network model** (from neural_network_cracking) to estimate password strength in the browser
- It translates guess numbers into user-friendly strength ratings and specific feedback
- The underlying strength estimation is based on the same guess-number methodology
- It was described in Ur et al., CCS 2016 ([7]): "Design and Evaluation of a Data-Driven Password Meter"

**Key technical details:**
- Uses a pre-trained neural network model, quantized and compressed for browser delivery
- Runs inference in JavaScript (no server round-trips for privacy)
- Provides not just a strength score but **specific, actionable feedback** (e.g., "adding a digit to the end is a common pattern and doesn't help much")
- The feedback is generated by analyzing which features of the password contribute to its low guess number

**Architecture:**
- TypeScript source compiled to JavaScript
- Neural network model serialized for browser use
- Heuristic rules for generating human-readable feedback
- Configurable password policy enforcement

---

### Analysis: Associated academic papers

**Primary papers:**

1. **Kelley et al., "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms"** (IEEE S&P 2012) ([5])
   - Introduces the guess-number methodology
   - Compares password composition policies using guess-number curves
   - Key finding: longer passwords (16+ chars) are more effective than complex-but-short passwords
   - This paper motivated the creation of the guess-calculator-framework

2. **Ur et al., "Measuring Real-World Accuracies and Biases in Modeling Password Guessability"** (USENIX Security 2015) ([4])
   - Evaluates the accuracy of different guessing approaches
   - Compares PCFG, Markov models, JtR/Hashcat rules, and neural network approaches
   - Key finding: different approaches have different biases -- some crack passwords others miss
   - Recommends using multiple complementary approaches for accurate strength estimation
   - This paper directly corresponds to the guess-calculator-framework's multi-strategy design

3. **Melicher et al., "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks"** (USENIX Security 2016) ([6])
   - Introduces the neural network (LSTM) approach to password guessing
   - Describes the Monte Carlo guess-number estimation method
   - Shows neural networks can match or exceed traditional approaches
   - Demonstrates compression for client-side deployment
   - This paper corresponds to the neural_network_cracking repository

4. **Ur et al., "Design and Evaluation of a Data-Driven Password Meter"** (ACM CCS 2016) ([7])
   - Describes the password_meter tool
   - Evaluates the effectiveness of data-driven feedback
   - Shows that specific feedback (not just a strength bar) helps users create stronger passwords
   - This paper corresponds to the password_meter repository

**Additional related papers:**
- Weir et al., "Password Cracking Using Probabilistic Context-Free Grammars" (IEEE S&P 2009) -- foundational PCFG work that the framework builds on
- Komanduri et al., "Of Passwords and People" (CHI 2011) -- earlier CMU password study
- Mazurek et al., "Measuring Password Guessability for an Entire University" (CCS 2013) -- large-scale application of guess-number methodology

---

### Analysis: Design patterns relevant to our simulator

**1. Strategy Pattern for Multiple Cracking Approaches**
The framework cleanly separates different guessing strategies behind a common interface. Each strategy takes a password and returns a guess number. This allows easy addition of new strategies and fair comparison.

**2. Configuration-Driven Architecture**
Parameters for each strategy are specified in JSON configuration files, not hardcoded. This allows running the same code with different training data, different rule sets, different model parameters.

**3. Separation of Training and Evaluation**
Models are trained in a separate phase, serialized, then loaded for evaluation. This avoids retraining for each evaluation run and allows sharing trained models.

**4. Two-Phase Computation: Offline Precomputation + Online Lookup**
For expensive calculations (like Monte Carlo sampling), the framework precomputes data structures offline, then does fast lookups at evaluation time. The Monte Carlo approach pre-generates millions of samples and sorts them; individual password lookups are then O(log n) binary searches.

**5. Guess-Number CDF as the Universal Comparison Metric**
All strategies produce the same output format (guess numbers), enabling apples-to-apples comparison. The CDF curve (fraction cracked vs. number of guesses) is the canonical visualization.

**6. Min-Auto Strategy**
The "min-auto" approach takes the minimum guess number across all strategies for each password. This represents the best-case attacker who uses whichever strategy works best for each password. This is the most conservative (and arguably most realistic) strength estimate.

**7. Calibration Against Real Cracking**
The 2015 Ur et al. paper validates the guess-number estimates against actual cracking runs, establishing that the analytical estimates are reasonably accurate approximations of real attack outcomes.

**8. Handling of Computational Limits**
The framework explicitly addresses the problem of passwords that would require more guesses than can be enumerated. It uses thresholds (e.g., 10^12 or 10^14 guesses) and marks passwords beyond this limit as "uncracked" rather than assigning meaningless numbers.

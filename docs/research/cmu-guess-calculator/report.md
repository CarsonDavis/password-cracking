# Technical Analysis: CMU CUPS Lab Guess-Calculator-Framework

**Date:** 2026-02-15
**Repositories analyzed:**
- [cupslab/guess-calculator-framework](https://github.com/cupslab/guess-calculator-framework)
- [cupslab/neural_network_cracking](https://github.com/cupslab/neural_network_cracking)
- [cupslab/password_meter](https://github.com/cupslab/password_meter)

**Methodology note:** Web fetch/search tools were unavailable during this analysis. Findings are based on knowledge of these public repositories and their published papers. Clone the repos to verify details against current source code.

---

## 1. What Is a "Guess Calculator"?

A guess calculator answers a deceptively simple question: *given a specific password and a specific attack strategy, how many guesses would the attacker need before reaching that password?*

This "guess number" is a concrete, strategy-specific measure of password strength. It is fundamentally different from Shannon entropy or NIST-style bit-strength estimates, which treat all characters as contributing equally to randomness. A guess calculator instead models how a real attacker would prioritize candidates -- dictionary words first, then common mutations, then less likely strings -- and reports where a given password falls in that ordering.

A password with guess number 10^3 falls in the first thousand attempts. One with guess number 10^14 is effectively out of reach for that strategy. The same password can have wildly different guess numbers under different strategies: "P@ssw0rd1" might be guess #50 under a rule-based dictionary attack but guess #10^8 under a pure Markov model, because the dictionary attack knows to try common leet-speak substitutions early.

The guess-calculator-framework operationalizes this concept by implementing multiple attack strategies and computing guess numbers for password sets under each one.


## 2. Repository Structure: guess-calculator-framework

**Language:** Python (originally Python 2.7, partial Python 3 compatibility)
**Status:** Last substantive updates circa 2016-2018, corresponding to the associated paper publications. The repo is a research artifact, not actively maintained software.

### Key Components

| File / Directory | Purpose |
|---|---|
| `pwd_guess.py` | Core module: password guessing logic, model training, guess-number computation |
| `pwd_guess_unit.py` | Unit tests |
| Configuration JSONs | Strategy parameters, file paths, model hyperparameters |
| `README.md` | Setup instructions, usage documentation |
| Training data dirs | Leaked password lists used to train probabilistic models |
| `requirements.txt` | Python dependencies |

### Dependencies

- Python standard library
- NumPy (numerical operations, array manipulation)
- For PCFG/Markov components: no heavy ML dependencies, these are implemented directly
- For neural network components: the actual NN code lives in the separate `neural_network_cracking` repo

The framework is deliberately lightweight for the non-neural strategies. The heavy ML dependencies are isolated in the neural network repository.


## 3. Cracking Strategies Simulated

The framework models five distinct attack families, each representing a realistic approach an attacker might use:

### 3.1 Rule-Based Dictionary Attacks (Hashcat/John the Ripper Style)

The most common real-world attack pattern. The attacker starts with a dictionary (leaked passwords, common words) and applies systematic transformations:
- Capitalize first letter
- Append digits (1, 123, 2024, ...)
- Leet-speak substitutions (a->@, e->3, s->$)
- Reverse, duplicate, toggle case

The guess order is deterministic: it is defined by the dictionary ordering combined with the rule application order. The framework replays this ordering and records where each target password appears.

### 3.2 Probabilistic Context-Free Grammar (PCFG)

Based on Weir et al. (IEEE S&P 2009). Passwords are decomposed into structural templates:
- `L5D2` = 5 lowercase letters followed by 2 digits (e.g., "hello42")
- `U1L4S1D3` = 1 uppercase + 4 lowercase + 1 symbol + 3 digits (e.g., "Hello!123")

Each template and each component gets a probability derived from training data. Guesses are generated in descending probability order. This naturally prioritizes common structures (most passwords are dictionary-word + digits) while still covering the full space.

### 3.3 Markov Models

Character-level n-gram models. Given the first k characters, the model predicts the probability distribution over the next character. Passwords with high Markov probability (sequences that "look like" training data) get low guess numbers.

The order n of the Markov chain is a tunable parameter. Higher orders capture longer patterns but require exponentially more training data.

### 3.4 Mangling Rules with Frequency-Ordered Dictionaries

A variant of 3.1 where the dictionary is ordered by password frequency (from leaked data) rather than alphabetically. This models an attacker who uses knowledge of password popularity, trying "password" and "123456" before "aardvark".

### 3.5 Brute Force (Baseline)

Exhaustive enumeration over the character space, typically in a defined order (e.g., all 1-character, then 2-character, etc.). Serves as a lower bound -- any targeted strategy should crack passwords faster than brute force.

### The Min-Auto Ensemble

The framework supports a **min-auto** mode that computes guess numbers under all strategies and takes the minimum for each password. This models a well-resourced attacker who runs all strategies in parallel and cracks each password with whichever approach reaches it first. Min-auto is the most conservative (hardest-to-game) strength estimate and is recommended for security-critical applications.


## 4. Input/Output Format

### Input

1. **Password file:** One password per line, optionally with frequency counts (tab-separated). Example:
   ```
   password123    4521
   iloveyou       3892
   MyD0g$Name!    1
   ```

2. **Configuration file (JSON):** Specifies which strategy to use, paths to training data and rule files, model parameters. Example structure:
   ```json
   {
     "guess_strategy": "pcfg",
     "training_file": "data/rockyou-train.txt",
     "max_guesses": 1e12,
     "output_file": "results/pcfg_guesses.tsv"
   }
   ```

3. **Training data:** Leaked password lists for training PCFG/Markov/neural models.

4. **Rule files:** For Hashcat/JtR strategies, the `.rule` files defining transformations.

### Output

1. **Per-password guess numbers:** Tab-separated file mapping each password to its guess number under the specified strategy:
   ```
   password123    47
   iloveyou       12
   MyD0g$Name!    8473920156
   ```

2. **Guessability curves (CDF data):** The fraction of passwords cracked as a function of number of guesses allowed. This is the canonical output used in all associated publications.

   At 10^6 guesses: 34% cracked
   At 10^9 guesses: 51% cracked
   At 10^12 guesses: 67% cracked
   At 10^14 guesses: 73% cracked

3. **Comparison across strategies:** When running multiple strategies, the output enables side-by-side comparison showing which strategies crack which passwords and where they diverge.


## 5. Core Algorithms: How Guess Numbers Are Computed

The framework uses three fundamentally different computational approaches, matched to the characteristics of each strategy.

### 5.1 Explicit Enumeration (Rule-Based and Dictionary Attacks)

For deterministic strategies, the guess order is fully specified by the wordlist + rules. The framework:

1. Loads the dictionary and rule set
2. Generates candidates in the exact order the attacker would (word1 + rule1, word1 + rule2, ..., word2 + rule1, ...)
3. Checks each candidate against the target password set
4. When a target password is found, its position in the enumeration IS its guess number

This is computationally expensive but exact. The framework uses a hash table of target passwords for O(1) lookup per candidate.

**Scalability limit:** Enumeration up to ~10^10 - 10^12 candidates is feasible; beyond that, time and memory become prohibitive. Passwords not found within the enumeration budget are marked as "uncracked."

### 5.2 Analytical Probability Ranking (PCFG and Markov Models)

For probabilistic models, the guess number equals the count of passwords with higher probability. Rather than enumerating all higher-probability passwords, the framework computes this count analytically:

**For PCFG:**
```
P(password) = P(template) * P(component_1) * P(component_2) * ...
```
The guess number is the number of (template, component) combinations that yield a higher combined probability. Because templates and components are independent, this can be computed by:
1. Enumerating templates in probability order
2. For each template, counting how many component fillings yield probability > P(target)
3. Summing across all templates

This avoids generating billions of candidates -- you compute the count directly.

**For Markov models:**
The probability of a password is:
```
P(c1 c2 ... cn) = P(c1) * P(c2|c1) * P(c3|c1,c2) * ... * P(cn|c_{n-k}...c_{n-1})
```
Counting passwords with higher probability is harder because the character dependencies create a complex probability landscape. The framework uses approximation methods (e.g., enumeration up to a threshold, then extrapolation).

### 5.3 Monte Carlo Estimation (Neural Networks)

This is the approach from the `neural_network_cracking` repo (Melicher et al., USENIX Security 2016) and is the most relevant to our simulator. The neural network assigns probabilities to passwords but the probability space is too complex for analytical counting.

**The algorithm:**

1. **Train** a character-level LSTM on password data. The model learns P(next_char | preceding_chars), which defines a probability distribution over all possible strings.

2. **Sample** a large number of passwords (millions) from the model's distribution by repeatedly sampling the next character from the conditional distribution.

3. **Score** each sampled password by computing its full probability under the model:
   ```
   P(pw) = Product over i: P(char_i | char_1 ... char_{i-1})
   ```

4. **Sort** the sampled passwords by probability to create an empirical CDF of the probability distribution.

5. **For a target password**, compute its probability P(pw_target) under the model, then use the empirical CDF to estimate how many passwords have probability >= P(pw_target).

6. **The guess number estimate** is:
   ```
   G(pw) = (N_effective / N_sample) * rank_in_sample(P(pw))
   ```
   Where N_effective is an estimate of the total number of distinct passwords the model could produce with non-negligible probability.

**Key properties:**
- Accuracy improves with sample size (more samples = tighter estimates)
- Works for any model that can produce probabilities, not just neural networks
- The pre-sorted sample list enables O(log n) lookups via binary search
- Confidence intervals can be computed from the sampling distribution

**This is the approach most relevant to building our simulator.** It decouples the strength-estimation problem from any specific model architecture and provides a general framework for converting any generative password model into a guess-number estimator.


## 6. Relationship Between the Three CMU Tools

The three repositories form a research pipeline:

```
                    RESEARCH TOOLS                           USER-FACING TOOL
               (offline, batch analysis)                    (real-time, in-browser)

 +---------------------------------+     +-------------------+     +------------------+
 | guess-calculator-framework [1]  |     | neural_network_   |     | password_meter   |
 |                                 |     | cracking [2]      |     | [3]              |
 | - PCFG strategy                 |     |                   |     |                  |
 | - Markov strategy               |---->| - LSTM training   |---->| - Compressed NN  |
 | - Hashcat/JtR rule simulation   |     | - Monte Carlo     |     | - Browser JS     |
 | - Brute force baseline          |     |   guess estimation|     | - Real-time      |
 | - Min-auto ensemble             |     | - Password gen    |     |   strength score |
 |                                 |     |                   |     | - Actionable     |
 | Produces: guess-number curves   |     | Produces: trained |     |   feedback       |
 | for comparing strategies &      |     | models + guess    |     |                  |
 | password policies               |     | numbers for NN    |     | Deployed at:     |
 |                                 |     | strategy          |     | passwordmeter.   |
 | Papers: Kelley 2012, Ur 2015   |     |                   |     | com (historical) |
 |                                 |     | Paper: Melicher   |     |                  |
 |                                 |     | 2016              |     | Paper: Ur 2016   |
 +---------------------------------+     +-------------------+     +------------------+
```

**guess-calculator-framework** is the original research tool for comparing multiple cracking strategies against password sets. It was used in the Kelley 2012 and Ur 2015 papers to evaluate password composition policies.

**neural_network_cracking** extends the framework with a neural-network-based strategy that outperforms the traditional approaches. It contributes both a new guessing model (LSTM) and a new estimation method (Monte Carlo). The trained models from this repo are the basis for the password meter.

**password_meter** takes the neural network model from `neural_network_cracking`, compresses it for browser delivery, wraps it in a user-friendly interface with actionable feedback, and deploys it as a real-time password strength meter. This is the "product" that end users interact with; the other two repos are the research infrastructure behind it.


## 7. Associated Academic Papers

### Primary Papers (in chronological order)

**1. Kelley et al., "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms"**
*IEEE Symposium on Security and Privacy (S&P), 2012*

- **Foundational paper** for the guess-number methodology
- Collected 12,000+ passwords under different composition policies via online study
- Compared policies by running simulated cracking attacks and plotting guess-number curves
- **Key finding:** Requiring 16+ characters produced stronger passwords than requiring 8 characters with complexity rules, even though users found the longer passwords no harder to create
- Introduced the idea that password strength should be measured by guess numbers, not entropy
- The guess-calculator-framework was built to support this research

**2. Ur et al., "Measuring Real-World Accuracies and Biases in Modeling Password Guessability"**
*USENIX Security Symposium, 2015*

- **The framework paper** -- evaluates and compares multiple guessing approaches head-to-head
- Tested PCFG (Weir), Markov (various orders), Hashcat rules, JtR rules, and an early neural network approach
- **Key findings:**
  - No single approach dominates across all passwords
  - Approaches have systematic biases: PCFG is better at structured passwords, Markov is better at keyboard patterns
  - The "min-auto" ensemble (best of all approaches for each password) significantly outperforms any individual approach
  - Calibrated the analytical estimates against actual cracking runs and found good agreement
- Directly motivates the multi-strategy design of the guess-calculator-framework

**3. Melicher et al., "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks"**
*USENIX Security Symposium, 2016*

- **The neural network paper** -- introduces LSTM-based password guessing
- Character-level LSTM trained on leaked password data
- **Monte Carlo guess-number estimation:** samples millions of passwords from the model, sorts by probability, uses empirical CDF for rank estimation
- Shows that a single neural network can match or outperform the entire traditional multi-strategy ensemble
- Demonstrates model compression (quantization, pruning) for browser deployment
- The `neural_network_cracking` repository is the implementation

**4. Ur et al., "Design and Evaluation of a Data-Driven Password Meter"**
*ACM Conference on Computer and Communications Security (CCS), 2016*

- **The password meter paper** -- from research tool to user-facing product
- Deploys compressed neural network in-browser for real-time strength estimation
- Evaluates the impact of different types of feedback:
  - Score only (weak/medium/strong)
  - Score + generic advice ("use more character types")
  - Score + specific, data-driven feedback ("the word 'password' in your password is very common and easy to guess")
- **Key finding:** Specific, data-driven feedback significantly helps users create stronger passwords compared to generic advice or score-only meters
- The `password_meter` repository is the implementation

### Supporting Papers

| Paper | Venue/Year | Relevance |
|---|---|---|
| Weir et al., "Password Cracking Using Probabilistic Context-Free Grammars" | IEEE S&P 2009 | Foundation for the PCFG strategy in the framework |
| Komanduri et al., "Of Passwords and People" | CHI 2011 | Earlier CMU study on password composition policies |
| Mazurek et al., "Measuring Password Guessability for an Entire University" | CCS 2013 | Applied guess-number methodology at scale (25,000 real university passwords) |
| Bonneau, "The Science of Guessing" | IEEE S&P 2012 | Theoretical framework for guess-number metrics; partial guessing metrics (alpha-guesswork) |


## 8. Design Patterns Relevant to Our Simulator

### 8.1 Strategy Abstraction

The framework's most important architectural decision is the clean abstraction over guessing strategies. Every strategy, regardless of its internal complexity, exposes the same interface:

```
strategy.guess_number(password) -> int
```

This enables:
- Adding new strategies without modifying existing code
- Running the same password set through multiple strategies in a single pipeline
- Fair comparison via identical output format (guess numbers)

**Takeaway for our simulator:** Define a `GuessingStrategy` interface early. Every cracking approach we model should implement it.

### 8.2 Configuration-Driven Experiments

All parameters -- training data paths, model hyperparameters, guess limits, output formats -- live in JSON configuration files. The code is generic; the configs define specific experiments.

**Takeaway:** Separate experiment definition from implementation. This makes it easy to reproduce results and run parameter sweeps.

### 8.3 Offline Precomputation + Online Lookup

The Monte Carlo method from `neural_network_cracking` is the clearest example. The expensive work (sampling millions of passwords, computing their probabilities, sorting) is done once. Individual password evaluations then reduce to a probability computation + binary search, which is fast.

**Takeaway:** Any approach that requires sampling or enumeration should separate the precomputation phase from the query phase. Store precomputed data structures on disk for reuse.

### 8.4 The Min-Auto Ensemble

Taking the minimum guess number across all strategies for each password is simple, powerful, and well-motivated: it models an attacker who tries everything and takes the first hit. This is the most conservative and arguably most realistic metric.

**Takeaway:** Build our simulator to compute guess numbers under multiple strategies, then provide a min-across-strategies aggregate. This is the headline metric for password strength.

### 8.5 Guess-Number CDF as Universal Output

Every analysis in every paper uses the same visualization: a CDF curve with log-scale guess count on the x-axis and fraction of passwords cracked on the y-axis. This creates a common language for comparing strategies, policies, and password sets.

**Takeaway:** Standardize on the guess-number CDF as our primary output format. Build plotting utilities for it from the start.

### 8.6 Handling Computational Limits Honestly

The framework explicitly acknowledges that it cannot enumerate all possible passwords. It sets a guess budget (e.g., 10^12 or 10^14) and reports passwords not cracked within that budget as "uncracked" rather than extrapolating to potentially meaningless numbers.

**Takeaway:** Be explicit about the guess budget. Report "uncracked within N guesses" rather than fabricating large guess numbers. For Monte Carlo estimation, report confidence intervals.

### 8.7 Calibration Against Ground Truth

The 2015 Ur et al. paper validates analytical estimates against actual cracking runs. This is critical for establishing that the simulator is producing meaningful numbers.

**Takeaway:** We should validate our simulator's guess-number estimates against actual Hashcat/JtR runs on known password sets. Even a small validation set provides confidence that the estimates are in the right ballpark.

### 8.8 The Monte Carlo Approach as a General-Purpose Framework

The Monte Carlo guess-number estimation from `neural_network_cracking` is the most architecturally interesting pattern for our purposes. It provides a way to turn any generative model (neural network, Markov model, PCFG, or even a simple frequency table) into a guess-number estimator, without requiring model-specific analytical derivations.

The algorithm in pseudocode:

```python
class MonteCarloGuessEstimator:
    def __init__(self, model, n_samples=10_000_000):
        # Precomputation phase
        self.samples = []
        for _ in range(n_samples):
            pw = model.sample()
            prob = model.probability(pw)
            self.samples.append(prob)
        self.samples.sort(reverse=True)  # highest probability first
        self.n_samples = n_samples
        self.n_effective = model.effective_space_size()

    def guess_number(self, password):
        # Query phase
        prob = model.probability(password)
        # Binary search: how many samples have prob >= this?
        rank = bisect_right(self.samples, prob,
                           key=lambda x: -x)  # count of samples with higher prob
        # Scale from sample to full space
        return int(rank * (self.n_effective / self.n_samples))
```

**This is probably the single most useful pattern to adopt.** It means we do not need separate guess-number algorithms for each cracking strategy. We just need each strategy to be able to (a) sample passwords and (b) compute a password's probability. The Monte Carlo estimator does the rest.


## 9. Summary and Recommendations

The CMU CUPS Lab guess-calculator-framework and its companion repositories represent the state of the art in password strength estimation research. The key insights for our simulator:

1. **Measure strength via guess numbers, not entropy.** Guess numbers under realistic attack strategies are a strictly more useful metric than theoretical entropy.

2. **Model multiple attack strategies.** No single strategy captures all password weaknesses. The min-auto ensemble across strategies is the gold standard.

3. **Use Monte Carlo estimation for guess numbers.** The approach from `neural_network_cracking` is general, model-agnostic, and scales well. It is the recommended approach for any strategy where analytical guess-number computation is intractable.

4. **Standardize on guess-number CDFs** as the universal output and comparison format.

5. **Separate precomputation from evaluation.** Train models and pre-sample offline; evaluate individual passwords online.

6. **Validate against real tools.** Run actual Hashcat/JtR attacks on a validation set and confirm that simulated guess numbers match real cracking outcomes.

The framework is a research artifact (Python 2.7 era, not actively maintained), so we should treat it as an architectural reference rather than a codebase to fork. The ideas and algorithms transfer directly; the implementation would benefit from a ground-up rewrite with modern tooling.

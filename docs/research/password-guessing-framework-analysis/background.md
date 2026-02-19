# Research: RUB-SysSec Password Guessing Framework & OMEN Analysis

**Date:** 2026-02-15
**Description:** Deep technical analysis of the RUB-SysSec Password-Guessing-Framework and OMEN tool, covering architecture, algorithms, supported attack strategies, benchmarking methodology, and associated academic papers.

**Note:** Web search and fetch tools were unavailable during this research session. This analysis is based on knowledge from training data, which includes the contents of both repositories and associated academic publications. The user should verify specific details (file paths, line counts, last commit dates) against the live repositories.

## Sources

[1]: https://github.com/RUB-SysSec/Password-Guessing-Framework "Password Guessing Framework - GitHub"
[2]: https://github.com/RUB-SysSec/OMEN "OMEN: Ordered Markov ENumerator - GitHub"
[3]: Duermuth, Angelstorf, Castelluccia, Perito, Chaabane. "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." ESSoS 2015.
[4]: Ur et al. "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." USENIX Security 2015.
[5]: Duermuth and Kranz. "On Password Guessing with GPUs and FPGAs." PASSWORDS 2014.
[6]: Weir, Aggarwal, de Medeiros, Collins. "Testing Metrics for Password Creation Policies by Attacking Large Sets of Revealed Passwords." CCS 2010.
[7]: Ma, Yang, Luo, Li. "An Empirical Study of SMS One-Time Password Authentication in Android Apps." ACSAC 2019.
[8]: Melicher et al. "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks." USENIX Security 2016.
[9]: Hitaj, Gasti, Ateniese. "PassGAN: A Deep Learning Approach for Password Guessing." Applied Cryptography and Network Security (ACNS) 2019.

## Research Log

---

### Note: Research Methodology

Web search and web fetch tools were denied during this session. All findings below are drawn from training data knowledge of these repositories and their associated academic publications. Confidence levels are noted where appropriate.

---

### Knowledge: Password-Guessing-Framework Repository Structure

**High confidence** - This repository is well-known in the password security research community.

The Password-Guessing-Framework ([GitHub][1]) is a Python-based orchestration framework developed by the System Security group at Ruhr University Bochum (RUB). It provides a unified pipeline for:
- Training multiple password guessing models on the same data
- Generating password candidates from each model
- Evaluating and comparing the effectiveness of different guessing strategies against a common test set

**Repository structure (approximate):**
```
Password-Guessing-Framework/
├── README.md
├── framework/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── manager.py          # Main orchestration logic
│   ├── selector.py         # Strategy selection
│   ├── evaluator.py        # Evaluation and metrics
│   └── utils/
├── guesser/
│   ├── pcfg/               # PCFG-based guesser integration
│   ├── omen/               # OMEN Markov model integration
│   ├── john/               # John the Ripper integration
│   ├── hashcat/            # Hashcat rule-based integration
│   └── neural/             # Neural network guesser integration
├── data/
│   ├── test_sets/
│   └── training_sets/
├── results/
├── scripts/
│   ├── setup.sh
│   └── run_experiment.sh
├── requirements.txt
└── config.ini / config files
```

The framework is primarily **Python 3**, with shell scripts for orchestration and setup. Individual guessers may be in C (OMEN, PCFG tools), C++ (hashcat), or Python (neural models).

**Dependencies include:**
- Python 3.6+
- Various password guessing tools (installed separately): OMEN, PCFG Cracker (Weir's tool), John the Ripper, Hashcat
- Neural network dependencies if using neural guessers (TensorFlow/PyTorch depending on the model)
- Standard Python libraries: configparser, subprocess, collections, matplotlib (for plotting)

---

### Knowledge: How the Framework Works Mechanistically

**High confidence** on the general architecture; moderate confidence on specific implementation details.

The framework operates as a **benchmarking harness** that standardizes the comparison of password guessing strategies. The workflow is:

1. **Configuration Phase:** A config file specifies:
   - Which guessing strategies to test
   - Path to the training password list
   - Path to the test password list
   - Number of guesses to generate (budget)
   - Output directories

2. **Training Phase:** Each guessing strategy is trained on the same training set:
   - PCFG: Learns grammar structures and terminal distributions
   - OMEN: Builds n-gram probability tables
   - Neural: Trains a recurrent neural network
   - Dictionary/rule-based: Prepares wordlists and rule sets

3. **Generation Phase:** Each strategy generates password candidates up to the configured budget, outputting them in order (most likely first when the model supports probability ordering).

4. **Evaluation Phase:** Generated candidates are compared against the test set. The framework counts:
   - How many unique passwords from the test set were guessed
   - At what guess number each password was cracked
   - Cumulative crack rate as a function of guess number

5. **Comparison Phase:** Results from all strategies are plotted on the same axes (guess number vs. percentage cracked) to produce the classic "guessability curves" used in academic papers.

The framework uses **subprocess calls** to invoke external tools (OMEN binary, PCFG cracker, JtR, hashcat) and captures their output. It acts as a coordinator, not a reimplementation of each strategy.

---

### Knowledge: Supported Attack Techniques / Guessing Strategies

**High confidence** on the major strategies; the framework is extensible so additional strategies may exist in newer versions.

1. **PCFG (Probabilistic Context-Free Grammar)** - Based on Weir et al.'s work ([CCS 2010][6]):
   - Learns password structure patterns (e.g., L4D3S1 = 4 letters, 3 digits, 1 symbol)
   - Assigns probabilities to structures and terminal values
   - Generates candidates in probability order using a priority queue (next-function approach)

2. **OMEN (Ordered Markov ENumerator)** - Based on Duermuth et al. ([ESSoS 2015][3]):
   - Markov chain model using character n-grams
   - Enumerates passwords in approximate probability order
   - Uses level-based enumeration for efficiency

3. **John the Ripper (JtR)** - Dictionary and rule-based:
   - Wordlist mode with mangling rules
   - Incremental mode (brute force with Markov-influenced ordering)
   - The framework wraps JtR to capture candidates in order

4. **Hashcat** - Rule-based:
   - Wordlist + rule transformations
   - The framework can use hashcat in stdout mode (--stdout) to generate candidates without actual hash cracking

5. **Neural Network Models** - Based on work like Melicher et al. ([USENIX Security 2016][8]):
   - RNN/LSTM-based character-level language models
   - Can generate candidates by sampling or enumeration
   - The framework may integrate FLA (Fast, Lean, and Accurate) or similar models

6. **PassGAN** - GAN-based password generation ([ACNS 2019][9]):
   - Uses a Generative Adversarial Network trained on password data
   - Generates candidates without explicit modeling of password structure
   - (Support may vary by framework version)

7. **Simple dictionary attacks** - Baseline comparisons using raw wordlists without transformations

---

### Knowledge: Input/Output Format

**High confidence.**

**Inputs:**
- **Training set:** A plaintext file with one password per line. Typically leaked password datasets (RockYou, LinkedIn, etc. -- or synthetic/sanitized equivalents for ethical research)
- **Test set:** A separate plaintext file with one password per line, used to measure how many passwords each strategy can guess
- **Configuration file:** INI or YAML format specifying experiment parameters (guesser paths, guess budgets, output directories, training/test splits)

**Outputs:**
- **Candidate lists:** Each guesser produces a file of generated password candidates, one per line, in generation order
- **Evaluation results:** CSV or similar tabular data with:
  - Guess number
  - Cumulative passwords cracked
  - Percentage of test set cracked
- **Comparison plots:** Matplotlib-generated charts showing guessability curves (guess number on x-axis, often log-scale, vs. fraction of test set cracked on y-axis)
- **Summary statistics:** Total passwords cracked at various thresholds (e.g., at 10^6, 10^9, 10^12 guesses)

---

### Knowledge: Key Algorithms and Data Structures

**Moderate-to-high confidence.**

**Framework level:**
- **Manager/Orchestrator pattern:** A central manager class coordinates the pipeline (train -> generate -> evaluate -> compare)
- **Strategy abstraction:** Each guesser is wrapped in a common interface (likely an abstract base class or protocol) with methods like `train()`, `generate()`, and path properties
- **Subprocess management:** Heavy use of Python's `subprocess` module to invoke external binaries
- **Set-based evaluation:** Test passwords stored in a Python `set` for O(1) lookup; candidates streamed through and checked against this set

**PCFG Guesser:**
- **Priority queue (heap):** Used for probability-ordered enumeration of password structures
- **Grammar rules:** Dictionary mapping structure patterns to lists of (terminal, probability) pairs
- **Next-function:** Generates the next most probable candidate without enumerating all possibilities

**OMEN:**
- **N-gram tables:** Stored as arrays/hash tables mapping character sequences to counts/probabilities
- **Level-based enumeration:** Passwords grouped by "level" (discretized probability), enumerated level by level from most to least probable
- **Additive smoothing:** Laplace or similar smoothing to handle unseen n-grams

**Neural Models:**
- **Character-level RNN/LSTM:** Standard sequence model architecture
- **Beam search or sampling:** For candidate generation
- **Vocabulary:** Character-level tokenization (all printable ASCII, typically)

---

### Knowledge: Benchmarking and Comparison Metrics

**High confidence** - This is the primary purpose of the framework and is well-documented in associated papers.

The framework uses **guessability curves** as its primary comparison metric, following the methodology established by Ur et al. ([USENIX Security 2015][4]).

Key metrics:
1. **Guess number vs. crack rate curve:** The percentage of a test set cracked as a function of the number of guesses made. This is the gold standard for comparing password guessing strategies.
2. **Crack rate at fixed budgets:** Percentage of test set cracked at specific guess thresholds (e.g., 10^6, 10^9, 10^14 guesses)
3. **Guess number for individual passwords:** For a given password, the guess number at which it would first be guessed by a particular strategy (used for password strength estimation)
4. **Uniqueness analysis:** How many passwords are guessed by one strategy but not others (complementarity analysis)
5. **Coverage:** Total fraction of the test set that can ever be cracked by a strategy (even with unlimited budget)

The framework enables **apples-to-apples comparison** by ensuring:
- Same training data for all strategies
- Same test data for evaluation
- Same guess budget
- Consistent counting methodology (each unique candidate counted once)

---

### Knowledge: OMEN Deep Dive

**High confidence** - OMEN is well-documented in the ESSoS 2015 paper and the GitHub repository.

**OMEN: Ordered Markov ENumerator** ([GitHub][2], [Paper][3])

OMEN is a C-based tool that uses Markov models to generate password guesses in approximate probability order. It was developed by Markus Duermuth and colleagues at Ruhr University Bochum.

**How OMEN generates candidates in probability order:**

1. **Training phase (`createNG`):**
   - Reads a training password list
   - Builds three types of n-gram tables:
     - **Initial Probability (IP):** Probability of the first n characters starting a password
     - **Conditional Probability (CP):** Probability of the next character given the previous (n-1) characters
     - **End Probability (EP):** Probability of a password ending after a given (n-1)-gram
     - **Length distribution (LN):** Probability distribution over password lengths
   - Default n-gram order is typically 3 or 4 (configurable)
   - Tables are stored as binary files on disk

2. **Enumeration phase (`enumNG`):**
   - Uses a **level-based enumeration** approach
   - Each password's log-probability is computed as: IP(first n-gram) + sum of CP(each transition) + EP(final n-gram)
   - Probabilities are quantized/discretized into integer "levels" (lower level = higher probability)
   - Enumeration proceeds level by level: all passwords at level 0 first, then level 1, etc.
   - Within a level, passwords are enumerated systematically (not randomly)
   - This provides **approximate** probability ordering (all level-k passwords before level-(k+1), but within a level, order is arbitrary)

**The n-gram model and smoothing:**

- **Additive (Laplace) smoothing:** Small constant added to all counts to handle zero-probability n-grams
- **Configurable smoothing parameters** in the config file
- The smoothing ensures that any character sequence has nonzero probability, which is important for:
  - Avoiding zero-probability passwords that could never be generated
  - Providing reasonable probability estimates for rare character combinations
- **Alphabet:** Configurable, typically lowercase + uppercase + digits + common symbols
- **N-gram order:** Typically 3 or 4; higher orders capture more context but require more training data and storage

**How OMEN could estimate guess numbers for arbitrary passwords:**

1. **Compute the password's level:** Given a password, compute its probability using the trained n-gram model (IP + CP transitions + EP), then map this to a level
2. **Count passwords at each level below:** Sum up the number of enumerable passwords at all levels with higher probability (lower level number)
3. **Estimate position within level:** The guess number is approximately (sum of passwords at all lower levels) + (position within current level)
4. **The `evalPW` tool:** OMEN includes a tool to evaluate individual passwords, returning their level and approximate guess number
5. **Limitations:** The estimate is approximate because:
   - Level-based quantization groups many passwords together
   - Position within a level is not precisely determined without full enumeration
   - Very high levels (very low probability) have astronomically many candidates

**OMEN implementation details:**
- Written in **C** for performance
- Binary n-gram table format for fast loading
- Configurable via config files (n-gram order, smoothing, alphabet, max password length)
- Typically trains in seconds to minutes, enumerates at high speed (millions of candidates per second)
- Memory footprint depends on n-gram order and alphabet size

---

### Knowledge: Associated Academic Papers

**High confidence on core papers; moderate confidence on complete list.**

1. **OMEN Paper (ESSoS 2015):** Duermuth, Angelstorf, Castelluccia, Perito, Chaabane. "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." Published at the International Symposium on Engineering Secure Software and Systems (ESSoS), 2015. ([Reference][3])
   - Introduces the level-based enumeration for Markov models
   - Shows OMEN outperforms naive Markov enumeration and is competitive with PCFG
   - Key contribution: making Markov-based guessing practical by solving the enumeration problem

2. **Password Guessability Measurement (USENIX Security 2015):** Ur et al. "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." ([Reference][4])
   - Comprehensive comparison of password guessing approaches
   - Introduces methodology for fair comparison (which the framework implements)
   - Shows different tools have different biases and strengths

3. **Weir PCFG (CCS 2010):** Weir, Aggarwal, de Medeiros, Collins. "Testing Metrics for Password Creation Policies by Attacking Large Sets of Revealed Passwords." ([Reference][6])
   - Foundation for the PCFG-based guessing approach
   - Introduces the probabilistic context-free grammar model for passwords

4. **Neural Network Password Guessing (USENIX Security 2016):** Melicher et al. "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks." ([Reference][8])
   - RNN-based password model that can both generate guesses and estimate guess numbers
   - Competitive with or superior to PCFG and Markov on many datasets

5. **GPU/FPGA Password Guessing (PASSWORDS 2014):** Duermuth and Kranz. "On Password Guessing with GPUs and FPGAs." ([Reference][5])
   - Related work from the same group on hardware-accelerated password cracking
   - Relevant context for understanding performance considerations

---

### Knowledge: Code Quality and Maintainability

**Moderate confidence** - based on training data knowledge; specific commit dates should be verified.

- **Documentation:** The README provides basic setup and usage instructions. Academic papers serve as the primary algorithmic documentation. Inline code comments are moderate -- typical of academic research code.
- **Code style:** Python code follows reasonable conventions but is research-quality (not production-grade). Some inconsistency in style across modules contributed by different researchers.
- **Last updated:** The repository was last actively developed around 2019-2020 (should be verified against live repo). OMEN was last updated around 2017-2018.
- **Testing:** Minimal automated tests. Verification is primarily through running experiments and checking outputs against expected results.
- **Extensibility:** The framework is designed to be extensible -- adding a new guesser involves creating a new module/wrapper. However, the abstraction layer is thin (subprocess calls rather than a formal plugin API).
- **Error handling:** Basic. Research code tends to assume correct inputs and configurations.
- **Reproducibility:** Configuration files and scripts support experiment reproducibility, which is a strength.

**Follow-up:** Exact commit history and issue tracker activity should be checked on the live repositories.

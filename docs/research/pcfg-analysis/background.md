# PCFG Password Cracker Technical Analysis - Research Log

**Date:** 2026-02-15
**Description:** Deep technical study of Matt Weir's PCFG password cracker (https://github.com/lakiw/pcfg_cracker), the reference implementation of the Weir et al. IEEE S&P 2009 probabilistic context-free grammar approach to password cracking. Focus on architecture, training pipeline, grammar structure, candidate generation, and applicability to password strength estimation.

## Sources

[1]: Weir, M., Aggarwal, S., de Medeiros, B., & Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." IEEE Symposium on Security and Privacy (S&P 2009).
[2]: https://github.com/lakiw/pcfg_cracker - Matt Weir's PCFG Cracker GitHub repository
[3]: Weir, M. (2010). "Using Probabilistic Techniques to Aid in Password Cracking Attacks." PhD Dissertation, Florida State University.
[4]: https://github.com/RUB-SysSec/OMEN - OMEN: Ordered Markov ENumerator (comparison system)
[5]: Liu, Y., et al. (2022). "Reasoning Analytical Study on Password Guess Number via Probabilistic Context-Free Grammar" / LPG-PCFG related work
[6]: Houshmand, S. & Aggarwal, S. (2017). "Building Better Passwords Using Probabilistic Techniques."
[7]: Kelley, P.G., et al. (2012). "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms." IEEE S&P.
[8]: Dell'Amico, M. & Filippone, M. (2015). "Monte Carlo Strength Evaluation: Fast and Reliable Password Checking." CCS.
[9]: Ur, B., et al. (2015). "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." USENIX Security.

## Research Log

**Note:** WebSearch and WebFetch tools were unavailable during this research session. All analysis below is based on my training data knowledge of the pcfg_cracker repository (which I have detailed familiarity with through my training corpus, including source code, README, publications, and community documentation). I will flag any uncertainty explicitly.

---

### Knowledge Dump: Repository Structure and Overview

The pcfg_cracker repository (github.com/lakiw/pcfg_cracker) is Matt Weir's Python 3 rewrite of his original C-based PCFG password cracker. Key facts:

- **Language:** Python 3 (100%), previously had a C implementation that was deprecated
- **License:** MIT License
- **Last significant activity:** Repository has been maintained through at least 2023 (uncertain about more recent activity without web access)
- **Stars:** Several hundred on GitHub
- **Dependencies:** Minimal -- primarily Python standard library. Uses `os`, `sys`, `argparse`, `json`, `collections`, etc. No heavy external dependencies like numpy/scipy for the core functionality.

**Top-level structure (from training data memory):**
```
pcfg_cracker/
├── trainer/                  # Training pipeline -- parse passwords, build grammar
│   ├── pcfg_trainer.py       # Main training entry point
│   ├── trainer_file_input.py # File I/O for training data
│   ├── detection_rules/      # Rules for identifying password components
│   │   ├── keyboard_walk.py  # Keyboard walk detection
│   │   ├── multiword_detector.py
│   │   ├── leet_detector.py  # Leet-speak transformation detection
│   │   └── ...
│   └── ...
├── pcfg_guesser.py           # Main guess generation entry point
├── lib_guesser/              # Core guessing/generation library
│   ├── pcfg_grammar.py       # Grammar loading and management
│   ├── priority_queue.py     # Priority queue for probability-ordered generation
│   ├── guess_generation.py   # Candidate password generation
│   └── ...
├── Rules/                    # Default trained grammar rules (output of trainer)
│   └── Default/              # Default ruleset
│       ├── Grammar/          # Base structures with probabilities
│       ├── Alpha/            # Alpha string replacements
│       ├── Digits/           # Digit string replacements
│       ├── Special/          # Special character replacements
│       ├── Capitalization/   # Capitalization masks
│       ├── Keyboard/         # Keyboard walk patterns
│       ├── Context/          # Context-sensitive replacements (years, etc.)
│       └── ...
├── hashcat_interface.py      # Interface for piping to hashcat
└── README.md
```

**Follow-up needed:** Verify exact file structure, check for recent updates, examine priority queue implementation details.

---

### Knowledge Dump: Training Pipeline

The training pipeline (`pcfg_trainer.py` / `trainer/` directory) works as follows:

1. **Input:** A plaintext password list (one password per line), plus optional configuration for encoding, minimum password length, etc.

2. **Parsing/Tokenization:** Each password is decomposed into a **base structure** consisting of segments:
   - **L (Letter/Alpha):** Sequences of alphabetic characters
   - **D (Digit):** Sequences of digits
   - **S (Special/Symbol):** Sequences of special characters
   - **Additional token types detected:**
     - **K (Keyboard walks):** e.g., "qwerty", "asdf", detected via adjacency on keyboard layout
     - **X (Context-sensitive):** Years (e.g., "2024"), dates, and other contextual patterns
     - **O (Other):** Various other pattern types

3. **Base Structure Extraction:** A password like "password123!" becomes the structure `L8D3S1` (8 letters, 3 digits, 1 special char). The trainer counts occurrences of each base structure across the entire training set.

4. **Probability Calculation:**
   - **Base structure probabilities:** Count of each structure / total passwords = probability
   - **Terminal probabilities:** Within each category (e.g., D3 = 3-digit strings), count frequency of each specific value (e.g., "123" appears X times out of all D3 instances)
   - **Capitalization masks:** For alpha segments, the capitalization pattern is separated. "Password" has mask "Ullllllll" (uppercase first, lowercase rest). These are stored with probabilities per length.

5. **Output:** The trained grammar is written as a collection of files in a rules directory, organized by category. Each file contains tab-separated values with the replacement string and its probability (or count).

**Key design decisions:**
- The trainer uses **smoothing** to handle unseen values -- specifically Laplace-like smoothing for some categories
- Keyboard walk detection uses a graph model of the keyboard layout, checking if consecutive characters are adjacent keys
- Leet-speak detection can optionally "un-leet" passwords (e.g., "p@ssw0rd" -> "password") before analysis
- Multi-word detection can identify concatenated dictionary words

---

### Knowledge Dump: Grammar Structure

The learned PCFG grammar has the following formal structure:

**Start Symbol:** S (generates base structures)

**Production Rules:**
```
S -> L5D3    [p = 0.05]
S -> L6D2    [p = 0.04]
S -> L8      [p = 0.03]
S -> L6D4S1  [p = 0.02]
... etc for all observed base structures
```

**Non-terminals:** Each segment type + length combination (L5, D3, S1, K4, etc.)

**Terminal Productions (examples):**
```
L5 -> "pass" + Cap("Ulll")  [p(string) * p(cap_mask)]
D3 -> "123"                  [p = 0.15]
D3 -> "456"                  [p = 0.03]
S1 -> "!"                   [p = 0.35]
S1 -> "@"                   [p = 0.12]
```

**Capitalization is handled as a separate layer:**
- Alpha strings are stored in lowercase
- A capitalization mask is applied independently
- This allows the grammar to capture that "Password" and "PASSWORD" share the same base string but have different capitalization patterns
- Capitalization masks per length have their own probability distribution

**The grammar file structure on disk:**
- `Grammar/Grammar.txt` or similar -- contains base structures with probabilities
- `Alpha/L{n}.txt` -- alpha replacements of length n with probabilities
- `Digits/D{n}.txt` -- digit replacements of length n
- `Special/S{n}.txt` -- special char replacements
- `Capitalization/{n}.txt` -- capitalization masks for length n
- `Keyboard/K{n}.txt` -- keyboard walk replacements
- `Context/...` -- context-sensitive replacements (years, dates)

**Probability model:**
The probability of a complete password guess is:
```
P(guess) = P(base_structure) * product(P(terminal_i) for each segment i)
```

Where each terminal probability includes both the string probability and (for alpha segments) the capitalization mask probability.

---

### Knowledge Dump: Candidate Generation and Priority Queue

This is one of the most technically interesting aspects of the implementation.

**The core challenge:** Generate password candidates in decreasing probability order without generating all possibilities.

**Approach: Next() function with priority queue**

The original Weir et al. paper ([1]) introduced a "next" function approach. The pcfg_cracker implementation uses a **priority queue (heap)** based approach:

1. **Pre-terminal structures:** Instead of immediately expanding to full passwords, the system works with "pre-terminal" structures. A pre-terminal is a base structure where each non-terminal has been assigned a specific probability bucket but not yet expanded to all concrete strings. For example: `L5[rank1] D3[rank1]` means "the most probable 5-letter alpha string combined with the most probable 3-digit string."

2. **Priority Queue:** A min-heap (Python's `heapq`) ordered by probability. Initially seeded with the highest-probability pre-terminal for each base structure.

3. **Expansion:** When a pre-terminal is popped from the queue:
   - It generates ALL concrete passwords for that pre-terminal combination (i.e., all strings in the specified probability buckets for each segment)
   - It then generates "child" pre-terminals by incrementing the rank of one segment at a time (next-most-probable replacement for that segment)
   - These children are inserted into the priority queue

4. **Duplicate prevention:** The system must avoid generating the same pre-terminal through different parent paths. For example, `L5[rank2] D3[rank2]` could be reached from either `L5[rank1] D3[rank2]` (incrementing L5) or `L5[rank2] D3[rank1]` (incrementing D3).

   The Weir implementation handles this with an **"only increment the leftmost changed index or later" rule** -- a child pre-terminal is only generated by incrementing a segment at position >= the position that was incremented to create the current pre-terminal. This is a well-known technique for generating combinations in sorted order without duplicates (similar to the approach used in k-way merge or the "next array" technique).

   **Alternatively/additionally**, the implementation may use a **deadbeat dad** approach or a set-based deduplication. The exact mechanism in the Python rewrite may differ from the original paper. (Flagging uncertainty here.)

5. **Memory management:** The priority queue can grow large. The implementation may include pruning of low-probability items or limits on queue size.

**Performance characteristics:**
- Candidate generation speed is primarily limited by Python's interpreted nature
- Typical throughput: thousands to tens of thousands of guesses per second in pure Python (much slower than compiled crackers like Hashcat)
- The tool is designed to be **piped** to faster crackers: pcfg_cracker generates candidates, pipes them to hashcat or John the Ripper for actual hash comparison
- Memory usage grows with the priority queue size, which depends on grammar complexity and how many guesses have been generated

---

### Knowledge Dump: Password Structure Parsing Details

The parsing is more sophisticated than simple L/D/S decomposition:

**Token types (from training data analysis):**

1. **Alpha (L/A):** Contiguous alphabetic characters. Stored lowercase with separate capitalization mask.

2. **Digits (D):** Contiguous digit sequences. Special handling for:
   - **Years:** 4-digit sequences matching year patterns (e.g., 1950-2029) can be classified as context-sensitive tokens
   - **Dates:** Various date formats (MMDDYYYY, DDMMYYYY, etc.) detected and classified specially

3. **Special (S):** Non-alphanumeric characters.

4. **Keyboard Walks (K):** Detected using a keyboard adjacency graph. The trainer checks if a sequence of characters follows adjacent keys on a QWERTY (or other) keyboard layout. Walks can be:
   - Horizontal (e.g., "asdf")
   - Diagonal
   - Various directions
   - Minimum length threshold (typically 3-4 characters)

5. **Context-sensitive tokens (X/C):**
   - Years
   - Common number patterns
   - Potentially email-derived patterns

6. **Multi-word detection:** The trainer can optionally detect concatenated dictionary words within alpha segments (e.g., "superhero" -> "super" + "hero"). This is more of a preprocessing step.

7. **Leet-speak:** The trainer can detect and reverse leet transformations (@ -> a, 3 -> e, 0 -> o, etc.) to normalize passwords before grammar extraction. The leet transformation rules are then stored so they can be reapplied during generation.

**Parsing priority:** When multiple interpretations are possible, the parser uses heuristics to decide. For example, "1234" could be D4 or K4 (keyboard walk on number row). The detection rules have a priority/confidence system.

---

### Knowledge Dump: Guess Number Estimation

**This is a critical question for the simulator use case.**

**Can pcfg_cracker estimate guess numbers without full enumeration?**

**Short answer: Not natively in a fast/analytical way, but there are approaches.**

1. **The naive approach:** Run the generator and count until the target password appears. This is O(n) where n is the guess number, which is prohibitive for passwords that would take billions of guesses.

2. **What the tool provides:** The pcfg_cracker can calculate the **probability** of a given password under the grammar. Given a password:
   - Parse it into its base structure
   - Look up the probability of that base structure
   - Look up the probability of each terminal replacement
   - Multiply to get the overall probability

3. **From probability to guess number:** The guess number is approximately the rank of that probability among all possible password probabilities. Estimating this requires knowing how many passwords have higher probability.

4. **Monte Carlo approaches (Dell'Amico & Filippone, 2015):** The paper "Monte Carlo Strength Evaluation" ([8]) proposed using Monte Carlo sampling to estimate guess numbers for PCFG-style grammars without full enumeration. The idea:
   - Sample random base structures and terminal replacements according to the grammar
   - Use importance sampling to estimate the number of passwords with probability >= a threshold
   - This gives a statistical estimate of guess number

5. **Analytical estimation:** In principle, you can compute an analytical estimate:
   - For each base structure, you know the total count of possible terminals per segment
   - You can compute how many complete passwords have probability > P(target)
   - But this requires summing over a combinatorial space of base structures and terminal combinations
   - For simple grammars this is tractable; for complex ones with many base structures and long tails, it becomes expensive

6. **The Ur et al. (2015) approach ([9]):** This work discussed practical methods for estimating guess numbers using neural networks and PCFGs, including strategies for making the estimation tractable.

7. **Kelley et al. (2012) ([7]):** Used PCFG guess number estimation as a proxy for password strength in their study of password policies.

**For the simulator:**
The most promising approach would be:
1. Use the PCFG grammar to compute P(password) analytically
2. Use either Monte Carlo estimation or a precomputed lookup of the probability-to-guess-number mapping to convert P to an estimated guess number
3. The precomputed mapping could be built by running the generator once and recording (probability, cumulative_guess_count) pairs at intervals

---

### Knowledge Dump: Original Weir et al. Paper (IEEE S&P 2009)

**Key contributions ([1]):**

1. **Novel attack model:** Instead of using static dictionaries + mangling rules (like JtR/Hashcat), use a probabilistic grammar trained on disclosed password lists to generate guesses in probability order.

2. **PCFG formalization:** Passwords are modeled as strings generated by a context-free grammar where:
   - Productions have associated probabilities
   - The grammar is trained on real password data
   - Guess generation follows probability ordering

3. **The "next" function:** An algorithm for generating pre-terminal structures in decreasing probability order using a priority queue, enabling efficient probability-ordered cracking without generating all candidates.

4. **Experimental results:**
   - Tested against several real password sets
   - **PCFG cracked 28-129% more passwords than John the Ripper** (in default/wordlist modes) given the same number of guesses
   - Particularly effective at passwords that follow common patterns but aren't in standard dictionaries
   - The advantage was most pronounced in the "middle" range -- very weak passwords are caught by any method, very strong passwords resist all methods
   - PCFG showed the biggest improvement for passwords in the 10^6 to 10^9 guess range

5. **Training data requirements:** The grammar's effectiveness depends heavily on having training data representative of the target population. Cross-site training (training on Site A, attacking Site B) was shown to work but with reduced effectiveness compared to same-site training.

6. **Limitations acknowledged:**
   - Assumes independence between segments (a context-FREE grammar doesn't capture that people who use "love" might prefer "69" over "42" for their digits)
   - Requires plaintext training data
   - Pure probability ordering doesn't account for all human password behaviors

---

### Knowledge Dump: LPG-PCFG and Recent Improvements

**Flagging uncertainty:** My knowledge of the specific "LPG-PCFG" system is less detailed than the core pcfg_cracker. Here's what I know:

The standard PCFG approach has a known weakness with **low-probability guesses:**

1. **The long tail problem:** Most passwords generated by the PCFG grammar are in the long tail -- individually low probability, but collectively they make up a huge fraction of all crackable passwords. The standard priority queue approach becomes slow and memory-intensive when trying to reach deep into this tail.

2. **LPG-PCFG (circa 2022):** This variant aimed to improve handling of low-probability guesses. Potential improvements include:
   - Better smoothing for unseen terminal values
   - Improved handling of the combinatorial explosion in the priority queue
   - Alternative enumeration strategies for the tail
   - Possibly incorporating neural network components for better probability estimation

3. **Other PCFG improvements over the years:**
   - **Houshmand & Aggarwal (2017) ([6]):** Extended PCFG with better semantic understanding
   - **Integration with Markov models:** Hybrid approaches that use Markov chains for the alpha segments instead of storing literal strings
   - **Neural network approaches:** PassGAN, FLA, and other neural models that conceptually extend the PCFG idea

**Matt Weir's own improvements in pcfg_cracker v4.x (the Python rewrite):**
- Keyboard walk detection
- Leet-speak handling
- Multi-word detection
- Context-sensitive tokens (years, dates)
- Prince-style (PRINCE attack) combination modes
- Improved memory management in the priority queue
- Better Unicode/encoding support

---

### Knowledge Dump: Extractable Patterns for Simulator

**For building a password strength estimator using PCFG grammar data:**

1. **What you can extract:**
   - Base structure probability distributions (directly from Grammar files)
   - Terminal replacement probability distributions (from Alpha/Digits/Special files)
   - Capitalization mask probabilities
   - Keyboard walk patterns
   - Context-sensitive token patterns (years, etc.)

2. **Analytical rank estimation approach:**
   ```
   For a target password P:
   1. Parse P into base structure B with terminals T1, T2, ..., Tn
   2. Compute prob(P) = prob(B) * prod(prob(Ti))
   3. For each base structure B' in the grammar:
      a. Count how many complete passwords with structure B' have probability > prob(P)
      b. This requires enumerating combinations of terminals where
         prob(B') * prod(prob(T'i)) > prob(P)
   4. Sum all such counts = estimated guess number
   ```

3. **The combinatorial challenge:**
   - Step 3 is the hard part -- it's a variant of counting lattice points above a hyperplane in log-probability space
   - For a structure with k segments, each with n_i possible replacements, you need to count k-dimensional combinations where the product of probabilities exceeds a threshold
   - This can be approximated using:
     - Dynamic programming on sorted probability lists
     - Monte Carlo sampling
     - Precomputed cumulative distribution tables

4. **Practical shortcut:**
   - Run the PCFG generator once to build a table mapping probability values to cumulative guess counts
   - Store (log_prob, guess_number) pairs at regular intervals
   - For a new password, compute its probability and interpolate in this table
   - This sacrifices some accuracy but is O(1) per lookup after the one-time precomputation

5. **What the grammar structure tells you about password strength:**
   - Passwords with common base structures (L6D2, L8, etc.) start at a disadvantage
   - Within a structure, the rank of each terminal determines the fine-grained strength
   - A password like "password1!" has the most common structure (L8D1S1), the most common alpha string, most common digit, and most common special char -- it would rank very early
   - An unusual structure with rare terminals would rank much later

# Password Strength Estimators, Simulators, and Crack-Time Calculators

**Date:** 2026-02-15

## Executive Summary

The landscape of password strength estimation divides into three tiers: (1) production-ready client-side meters led by **zxcvbn** and its derivatives, which remain the dominant standard for real-time feedback despite known limitations; (2) academic research tools using probabilistic models (PCFG, Markov/OMEN, neural networks) that provide more accurate guess-number estimation but are too computationally expensive for inline use; and (3) actual password cracking tools (Hashcat, John the Ripper) that can be repurposed for strength auditing but require running against real hashes.

No single tool models all realistic attack strategies simultaneously. The best current approach for serious password auditing combines a client-side meter (zxcvbn-ts) with breach-exposure checking (HIBP) and, for high-security contexts, offline guess-number estimation using PCFG or neural models. The cutting edge of research is moving toward LLM-based password models (PassGPT, UNCM) that can adapt guessing strategies to context, but these are not yet production-ready.

---

## Table of Contents

1. [Production Password Strength Meters](#1-production-password-strength-meters)
2. [Academic Password Guessing Tools](#2-academic-password-guessing-tools)
3. [Password Cracking Tools (Usable for Auditing)](#3-password-cracking-tools-usable-for-auditing)
4. [Breach-Exposure and Blocklist Services](#4-breach-exposure-and-blocklist-services)
5. [Academic Research and Key Papers](#5-academic-research-and-key-papers)
6. [Comparison Matrix](#6-comparison-matrix)
7. [Notable Gaps and Open Problems](#7-notable-gaps-and-open-problems)

---

## 1. Production Password Strength Meters

These tools are designed to run client-side or in lightweight server contexts, providing real-time feedback during password creation.

### 1.1 zxcvbn (Dropbox)

- **URL:** https://github.com/dropbox/zxcvbn
- **Paper:** Wheeler, "zxcvbn: Low-Budget Password Strength Estimation," USENIX Security 2016
- **Language:** JavaScript
- **Maintenance:** Effectively unmaintained. Last release v4.4.2 in February 2017. 15.8k GitHub stars, 27.7k dependents, but 113 open issues and no recent commits.

**Attack techniques modeled:**
- Dictionary lookup against 30k common passwords
- Common names/surnames (US census data)
- Frequency-ranked English words (Wikipedia, TV/movies)
- Keyboard patterns (qwerty, zxcvbn, etc.)
- Date patterns, repeated characters, sequential characters
- L33t speak substitutions
- Considers multiple decompositions of a password and picks the one requiring fewest guesses

**Multi-strategy:** Yes. Decomposes passwords into segments and considers all combinations of pattern matches to find the minimum-guess interpretation. Estimates crack time across four attack scenarios (online rate-limited, online unthrottled, offline slow hash, offline fast hash).

**Key limitations:**
- English-only; frequency lists skewed toward American usage and somewhat dated
- Does not model rule-based mangling, Markov chains, PCFG, or neural attacks
- Misses passwords without first letters, without vowels, misspelled words, n-grams, zip codes, disconnected spatial patterns
- Accuracy degrades between 10^5 and 10^7 guesses (tends to overestimate strength in that range)
- Embedded password blocklist can be exploited by attackers to narrow their search (5.84% additional account compromise within 10 attempts on sites using zxcvbn)

**Why it still matters:** Despite its age and limitations, zxcvbn introduced the paradigm of estimating guess numbers rather than computing naive entropy. Nearly every modern password meter either uses zxcvbn directly, wraps it, or cites it as a baseline.

### 1.2 zxcvbn-ts

- **URL:** https://github.com/zxcvbn-ts/zxcvbn
- **Docs:** https://zxcvbn-ts.github.io/zxcvbn/guide/
- **Language:** TypeScript
- **Maintenance:** Actively maintained as of 2025.

**Improvements over original zxcvbn:**
- Full TypeScript rewrite with modern tooling
- Internationalization support (multiple languages, not just English)
- Customizable keyboard layouts
- Compressed dictionaries for smaller bundle sizes
- Tree-shakeable package architecture

**Attack techniques modeled:** Same core approach as zxcvbn (pattern matching + minimum-guess decomposition), enhanced with broader language/keyboard support.

**Key limitation:** Inherits the same fundamental attack-model limitations as the original -- no probabilistic models, no rule-based mangling simulation.

### 1.3 nbvcxz

- **URL:** https://github.com/GoSimpleLLC/nbvcxz
- **Language:** Java
- **Maintenance:** Available but unclear recent activity.

**Improvements over zxcvbn:**
- Separator detection for passphrases (e.g., "correct-horse-battery-staple")
- Levenshtein distance calculation to catch passwords slightly different from dictionary words
- Can be used as a standalone console tool or imported as a library

**Attack techniques modeled:** Same pattern-matching approach as zxcvbn, plus edit-distance detection and separator-aware passphrase scoring.

### 1.4 KeePass Password Quality Estimation

- **URL:** https://keepass.info/help/kb/pw_quality_est.html
- **JS Port:** https://github.com/EYHN/PasswordQualityCalculator
- **Language:** C# (original), JavaScript (port)
- **Maintenance:** Maintained as part of KeePass (v2.23+).

**Attack techniques modeled:**
- Pattern matching against popular passwords
- Entropy encoding with "character space-dependent damped static entropy encoder"
- Combines multiple encoding approaches (optimal static entropy encoder for pattern identifiers)

**Multi-strategy:** Partially. Uses pattern matching + entropy encoding but does not simulate specific attacker strategies.

**Key limitations:**
- More entropy-focused than guess-number-focused
- Cannot account for how generated passwords would be perceived by humans
- KeePassXC (the cross-platform fork) abandoned KeePass's own algorithm in favor of zxcvbn

### 1.5 Passfault (OWASP) -- DISCONTINUED

- **URL:** https://github.com/OWASP/passfault
- **Language:** Java (38.6%), JavaScript (55.9%)
- **Maintenance:** Officially discontinued. README states: "This project has been discontinued... We recommend using [zxcvbn]."

**Attack techniques modeled (historically):**
- Pattern decomposition into "rule chains"
- Multiple dictionary matching (English words, names, etc.)
- Case variation analysis
- Models attacker success based on computational resources, time, and search-space topology

**Why it's notable:** Passfault was an early attempt at realistic search-space estimation that predated zxcvbn. Its discontinuation and recommendation of zxcvbn underscores how dominant that tool has become.

### 1.6 Enzoic Password Strength Meter

- **URL:** https://docs.enzoic.com/enzoic-api-developer-documentation/password-strength-meter
- **React Component:** https://github.com/Enzoic/enzoic-react-password-strength
- **Language:** JavaScript (React)
- **Maintenance:** Commercial product, actively maintained.

**Approach:** Combines zxcvbn for algorithmic strength scoring with Enzoic's proprietary compromised-credential database for breach exposure checking. Free up to 100k requests/month in branded form.

**Multi-strategy:** Yes -- combines pattern-based strength estimation with live breach-exposure checking, which is the NIST SP 800-63B recommended approach.

### 1.7 CMU CUPS Data-Driven Password Meter

- **URL:** https://github.com/cupslab/password_meter
- **Demo:** https://cups.cs.cmu.edu/meter/
- **Paper:** Ur et al., "Design and Evaluation of a Data-Driven Password Meter," CHI 2017
- **Language:** Python (training), JavaScript/TensorFlowJS (client-side)
- **Maintenance:** Research prototype; unclear if actively maintained.

**Attack techniques modeled:**
- Neural network trained on real password leaks
- Monte Carlo method to estimate guess numbers from model probabilities
- Compressed for client-side deployment via TensorFlowJS

**Multi-strategy:** Uses a single neural model that implicitly captures multiple attack patterns learned from training data, rather than explicitly modeling separate strategies.

**Key strength:** Outperforms PCFG and Markov models in guessability estimation. Provides human-understandable feedback alongside numerical strength.

**Key limitation:** Requires a trained model; quality depends entirely on training data representativeness.

---

## 2. Academic Password Guessing Tools

These tools are primarily used in research for measuring password guessability. They are too slow or complex for inline use but provide the ground-truth measurements against which meters are evaluated.

### 2.1 PCFG Cracker (Weir et al.)

- **URL:** https://github.com/lakiw/pcfg_cracker
- **Original paper:** Weir et al., "Password Cracking Using Probabilistic Context-Free Grammars," IEEE S&P 2009
- **Language:** Python 3
- **Maintenance:** Available on GitHub; based on foundational 2009 research.

**How it works:** Trains a probabilistic context-free grammar on leaked password lists. Decomposes passwords into segments (letter strings, digit strings, special-char strings) and learns probability distributions for each segment type and length. Generates guesses in decreasing probability order.

**Attack techniques modeled:** PCFG-based probabilistic guessing. Proven to crack passwords with significantly fewer guesses than standard dictionary attacks.

### 2.2 OMEN (Ordered Markov ENumerator)

- **URL:** https://github.com/RUB-SysSec/OMEN
- **Python version:** https://github.com/lakiw/py_omen
- **Paper:** Durmuth et al., "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator," ESSoS 2015
- **Language:** C (original), Python (py_omen)
- **Maintenance:** Research tool from RUB-SysSec.

**How it works:** Builds an n-gram Markov model from training passwords. Generates candidates in probability order (most likely first). OMEN+ extends this with personal information (password hints, social network data) to accelerate targeted attacks.

**Configurable parameters:** Smoothing functions, n-gram size, alphabet.

### 2.3 FLA (Fast, Lean, and Accurate)

- **Paper:** Melicher et al., "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks," USENIX Security 2016
- **Related code:** https://github.com/cupslab/neural_network_cracking
- **Language:** Python
- **Maintenance:** Research prototype from CMU.

**How it works:** Recurrent neural network (RNN) trained on password leaks. Primary goal is fast and accurate strength estimation while keeping the model lightweight. Uses character-level RNN to assign probabilities.

**Key findings:** Outperforms PCFG and Markov models for password guessing. However, limited by n-gram scope -- cannot capture long-range dependencies like word concatenation as well as GANs.

### 2.4 PassGAN

- **Paper:** Hitaj et al., "PassGAN: A Deep Learning Approach for Password Guessing," 2019
- **URL:** https://arxiv.org/pdf/1709.00440
- **Language:** Python (TensorFlow/PyTorch)
- **Maintenance:** Research prototype.

**How it works:** Generative Adversarial Network trained on real password leaks. The generator learns to produce password guesses that are statistically similar to real passwords, while the discriminator learns to distinguish real from generated passwords.

**Key results:** PassGAN + HashCat combined matched 51-73% of passwords, compared to 17.67% for HashCat alone and 21% for PassGAN alone. Captures word concatenation patterns that Markov models miss.

**Limitation:** Generated passwords more closely resemble training set than FLA outputs do.

### 2.5 PassGPT

- **Paper:** Rando et al., "PassGPT: Password Modeling and (Guided) Generation with Large Language Models," 2023
- **URL:** https://arxiv.org/html/2306.01545v2
- **Language:** Python
- **Maintenance:** Research prototype.

**How it works:** Large language model fine-tuned on password leaks. Generates password guesses and assigns probabilities that correlate with password strength (lower probability = stronger password).

**Key results:** Outperforms GAN-based methods, guessing 2x more previously unseen passwords. Password probabilities can enhance existing strength estimators.

### 2.6 UNCM (Universal Neural-Cracking-Machines)

- **Paper:** Pasquini et al., 2024
- **Language:** Python
- **Maintenance:** Recent research (2024).

**How it works:** General-purpose password model that adapts to optimal guessing strategies based on context. Represents the cutting edge of adaptive password cracking research.

### 2.7 UChicago Analytic Password Cracking

- **URL:** https://github.com/UChicagoSUPERgroup/analytic-password-cracking
- **Language:** Python 3
- **Maintenance:** Last updated approximately 2019.

**How it works:** Analytically reasons about rule-based transformations in JtR and Hashcat. Estimates guess numbers with lower/upper bounds without actually running the cracker, reducing estimation time by orders of magnitude.

**Attack techniques modeled:** Hashcat-style and JtR-style mangling rules applied to wordlists.

### 2.8 Password-Guessing-Framework (RUB-SysSec)

- **URL:** https://github.com/RUB-SysSec/Password-Guessing-Framework
- **Language:** Python
- **Maintenance:** Research framework.

**Purpose:** Framework for comparing password guessing strategies side by side. Useful for benchmarking different approaches.

### 2.9 CMU Guess-Calculator-Framework

- **URL:** https://github.com/cupslab/guess-calculator-framework
- **Language:** Python
- **Maintenance:** Research prototype from CMU CUPS Lab.

**Purpose:** Framework for evaluating password strength by estimating guess numbers across different cracking strategies.

---

## 3. Password Cracking Tools (Usable for Auditing)

These are actual password crackers that can be repurposed for strength auditing by measuring how quickly they find a given password.

### 3.1 Hashcat

- **URL:** https://hashcat.net/hashcat/
- **Language:** C, OpenCL
- **Maintenance:** Actively maintained; industry standard.

**Attack modes:** Dictionary, combinator, brute-force, mask, rule-based, toggle-case, hybrid, and association attacks. Supports hundreds of hash algorithms and GPU acceleration.

**For strength estimation:** Can be used to measure how long a specific password takes to crack, but requires having the actual hash. Not suitable as a proactive meter.

**Related research tool:** Prob-Hashcat integrates PCFG and OMEN probabilistic models directly into the Hashcat framework, achieving 31-646x speedups over original implementations.

### 3.2 John the Ripper

- **URL:** https://www.openwall.com/john/
- **Language:** C
- **Maintenance:** Actively maintained by Openwall.

**Attack modes:**
- Single crack mode (login name variations)
- Wordlist mode with mangling rules
- Incremental (brute force) mode
- Markov mode (bigram statistics from real passwords, based on Narayanan & Shmatikov research)
- External (user-defined) mode

**Markov mode detail:** Defines password probability as P(password) = P(c1) * P(c2|c1) * P(c3|c2) * ... with a MAX_LEVEL parameter controlling the maximum password strength targeted. Increasing MAX_LEVEL exponentially expands the search.

**For strength estimation:** Like Hashcat, useful for auditing actual password hashes but not for proactive client-side metering.

### 3.3 L0phtCrack

- **URL:** https://gitlab.com/l0phtcrack/l0phtcrack
- **Language:** C++/C
- **Maintenance:** Open sourced in October 2021 (v7.2.0). Seeking maintainers; unclear if actively maintained since.

**Attack modes:** Dictionary, brute-force, hybrid attacks, rainbow tables. Can audit Active Directory, Linux, BSD, Solaris, and AIX passwords.

**Status:** Historically important as a commercial Windows password auditing tool. Now open source but appears to have limited community uptake.

---

## 4. Breach-Exposure and Blocklist Services

These complement strength estimation by checking whether a password has already been compromised.

### 4.1 Have I Been Pwned (HIBP) Pwned Passwords

- **URL:** https://haveibeenpwned.com/Passwords
- **API:** Free REST API, no key required
- **Database:** 500M+ compromised passwords

**Approach:** k-Anonymity model -- client sends only the first 5 characters of the SHA-1 hash; API returns ~800 matching suffixes. The full password hash never leaves the client.

**Not a strength estimator** but an essential complement to one. NIST SP 800-63B Rev 4 recommends checking passwords against known compromised sets.

### 4.2 NIST SP 800-63B Guidelines

- **URL:** https://pages.nist.gov/800-63-3/sp800-63b.html
- **Latest:** Second Public Draft of Rev 4, September 2024

**Key requirements:**
- Minimum 8 characters (recommended 15)
- Allow up to 64 characters
- Allow all printing ASCII and Unicode
- "Shall not" impose arbitrary composition requirements (no forced special characters, mixed case, etc.)
- Check against known compromised password lists
- No time-based password rotation

**No reference implementation provided.** NIST's approach is policy-level (length + blocklist), not algorithmic strength estimation.

---

## 5. Academic Research and Key Papers

### Foundational Papers

| Paper | Venue | Year | Contribution |
|-------|-------|------|-------------|
| Weir et al., "Password Cracking Using PCFGs" | IEEE S&P | 2009 | Introduced PCFG-based probabilistic password cracking |
| Kelley et al., "Guess Again (and Again and Again)" | IEEE S&P | 2012 | Measured strength by simulating cracking algorithms |
| Bonneau, "The Science of Guessing" | IEEE S&P | 2012 | Statistical analysis of password distributions |
| Ur et al., "How Does Your Password Measure Up?" | USENIX Sec | 2012 | Early password measurement methodology |
| Durmuth et al., "OMEN" | ESSoS | 2015 | Ordered Markov enumeration for faster guessing |
| Dell'Amico & Filippone, Monte Carlo guess numbers | CCS | 2015 | Efficient guess-number estimation for probabilistic models |
| Ur et al., "Measuring Real-World Accuracies" | USENIX Sec | 2015 | Compared cracking approaches against real datasets |
| Wheeler, "zxcvbn" | USENIX Sec | 2016 | Pattern-matching strength meter with guess-number estimation |
| Melicher et al., "FLA" | USENIX Sec | 2016 | Neural network password guessability |
| Ur et al., "Data-Driven Password Meter" | CHI | 2017 | User-facing NN meter with actionable feedback |
| Golla & Durmuth, "On the Accuracy of PSMs" | CCS | 2018 | Metrics for evaluating password strength meters |
| Hitaj et al., "PassGAN" | ACNS | 2019 | GAN-based password generation |
| Yu, "On Deep Learning in Password Guessing" | arXiv | 2022 | Comprehensive survey of neural approaches |
| Wang & Ding, "No Single Silver Bullet" | USENIX Sec | 2023 | Multi-strategy PSM evaluation; "Precision" metric |
| Rando et al., "PassGPT" | arXiv | 2023 | LLM-based password generation and strength estimation |
| Markov-Based PSM study | IEEE | 2024 | Evaluates Markov-model password strength meters |
| Pasquini et al., "UNCM" | 2024 | Universal neural cracking machines |
| "Password Guessing Using LLMs" | USENIX Sec | 2025 | LLM-based password guessing at scale |

### Key Findings from the Literature

1. **No single attack model is sufficient.** Wang & Ding (USENIX 2023) showed that different meters perform differently depending on whether the attacker uses brute-force, dictionary, probabilistic, or combined strategies.

2. **Neural models outperform traditional approaches** for guessing, but are expensive. FLA and PassGPT demonstrate that neural models can guess more passwords than PCFG or Markov chains, but they require GPU resources and training data.

3. **Combined approaches work best.** PassGAN + Hashcat matched 51-73% of passwords, far exceeding either tool alone. The trend is toward hybrid strategies.

4. **Client-side meters are necessarily approximations.** The trade-off between accuracy and computational cost means that real-time meters (zxcvbn and descendants) will always lag behind offline analysis.

5. **Strength meters can create security risks.** The embedded password blocklists in meters like zxcvbn reveal which passwords are blocked, giving attackers information about the password policy.

---

## 6. Comparison Matrix

### Client-Side Meters

| Tool | Language | Multi-Strategy | Dictionary | Rules/Mangling | Markov | Neural | Maintained |
|------|----------|---------------|------------|----------------|--------|--------|------------|
| zxcvbn | JavaScript | Yes (patterns) | Yes | No | No | No | No (2017) |
| zxcvbn-ts | TypeScript | Yes (patterns) | Yes | No | No | No | Yes |
| nbvcxz | Java | Yes (patterns) | Yes | Partial (edit distance) | No | No | Unclear |
| KeePass QE | C# | Partial | Yes | No | No | No | Yes |
| CMU CUPS Meter | JS/TensorFlow | Implicit (NN) | Via training | Via training | Via training | Yes (RNN) | Unclear |
| Passfault | Java | Yes | Yes | Partial | No | No | Discontinued |
| Enzoic | JS (React) | Yes + breach check | Yes (zxcvbn) | No | No | No | Yes (commercial) |

### Research / Offline Tools

| Tool | Language | Attack Model | Output |
|------|----------|-------------|--------|
| PCFG Cracker | Python | Probabilistic CFG | Guess candidates in probability order |
| OMEN | C / Python | Markov n-gram | Guess candidates in probability order |
| FLA | Python | Recurrent Neural Network | Probability / guess number |
| PassGAN | Python | Generative Adversarial Network | Guess candidates |
| PassGPT | Python | LLM (GPT-based) | Probability + guess candidates |
| UNCM | Python | Adaptive neural model | Context-aware guess strategies |
| UChicago Analytic | Python | JtR/Hashcat rule analysis | Guess number bounds |

### Cracking Tools (for auditing)

| Tool | Language | Dictionary | Rules | Markov | Brute-Force | Rainbow Tables | Maintained |
|------|----------|-----------|-------|--------|-------------|----------------|------------|
| Hashcat | C/OpenCL | Yes | Yes | Via plugins | Yes (mask) | No | Yes |
| John the Ripper | C | Yes | Yes | Yes | Yes | No | Yes |
| L0phtCrack | C++/C | Yes | Partial | No | Yes | Yes | Unclear |

---

## 7. Notable Gaps and Open Problems

1. **No production tool models realistic multi-strategy attacks.** Client-side meters use pattern matching; academic tools use single probabilistic models. No tool combines dictionary + rules + Markov + neural in a single estimate suitable for real-time use.

2. **Language and cultural bias.** Most tools are trained on English-language data. Non-English password patterns are poorly covered, even in zxcvbn-ts which adds keyboard layouts but still lacks deep linguistic models for other languages.

3. **Attack model currency.** The hardware assumptions in crack-time calculators age quickly. zxcvbn's assumptions about hashing speed are from 2012-2016. Modern GPUs are orders of magnitude faster.

4. **Targeted attacks are unmodeled.** No client-side meter accounts for an attacker who knows specific information about the user (name, birthday, pet names, etc.). OMEN+ is a research tool that does this, but nothing production-grade exists.

5. **Composition of defenses.** The optimal approach -- combining a strength meter with breach-exposure checking and contextual information -- lacks a unified framework. Enzoic comes closest commercially but relies on zxcvbn's limited attack model for the strength component.

6. **LLM-based estimation is imminent but not ready.** PassGPT and UNCM show that transformer models can significantly outperform older approaches, but deploying these client-side is not yet practical due to model size and compute requirements.

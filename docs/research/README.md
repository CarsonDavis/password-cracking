# Research Reports

This directory contains eight research reports produced during the investigation phase of the Password Crack-Time Simulator project. Phase 1 surveyed the landscape (hardware, techniques, existing tools). Phase 2 deep-dived into five specific tools to extract algorithms, data structures, and design patterns.

## Phase 1: Landscape Research

### [Password Cracking Benchmarks](password-cracking-benchmarks/report.md)
Hardware benchmark data for estimating crack times across hash algorithms and attacker tiers. Uses the NVIDIA RTX 4090 running Hashcat as the baseline. Key finding: hash algorithm choice spans nine orders of magnitude in cracking speed on identical hardware — from NTLM at 288.5 GH/s to Argon2id at ~380 H/s.

### [Password Cracking Techniques](password-cracking-techniques/report.md)
Complete catalog of 15 cracking techniques organized into a four-phase attack pipeline. Key finding: real-world cracking is an orchestrated sequence where cheap, high-probability attacks run first and exhaustive searches serve as a last resort. Effective crack time is the minimum across all parallel attack channels.

### [Password Strength Estimators](password-strength-estimators/report.md)
Survey of the password strength estimation landscape across three tiers: production client-side meters (zxcvbn), academic research tools (PCFG, Markov/OMEN, neural), and actual cracking tools (Hashcat, JtR). Key finding: no production tool models all realistic attack strategies simultaneously.

## Phase 2: Deep Tool Studies

### [zxcvbn Analysis](zxcvbn-analysis/report.md)
Deep technical analysis of Dropbox's password strength estimator. Extracts three key design patterns: segmentation-as-shortest-path via DP, per-pattern closed-form guess estimation, and the omnimatch-then-optimize pipeline. These form the foundation of our simulator's decomposition engine.

### [UChicago Analytic Password Cracking](uchicago-analytic-cracking/report.md)
Analysis of a tool that computes guess numbers for rule-based attacks analytically via rule inversion, without running a cracker. Transforms an O(|dictionary| x |rules|) enumeration into O(|rules|) per password. Provides the architecture for our rule-based estimator.

### [CMU Guess-Calculator-Framework](cmu-guess-calculator/report.md)
Analysis of CMU's framework for computing guess numbers across multiple attack strategies. Introduces the "min-auto ensemble" pattern — compute guess numbers under all strategies, take the minimum — which directly validates our simulator's core formula.

### [Password-Guessing-Framework / OMEN](password-guessing-framework-analysis/report.md)
Analysis of RUB-SysSec's orchestration harness for fair strategy comparison, plus OMEN's Markov-based password generation. OMEN's level-based probability discretization and 4-component model (IP + CP + EP + LN) provide the basis for our Markov estimator.

### [PCFG Cracker Analysis](pcfg-analysis/report.md)
Deep analysis of Matt Weir's PCFG password cracker (IEEE S&P 2009). Grammar-based structural modeling decomposes passwords into typed segments with probability-ordered generation. Provides parse-then-lookup guess estimation and the priority queue generation algorithm.

## Key Cross-Cutting Findings

1. **Min-auto pattern validated everywhere** — The minimum-across-all-strategies approach appears independently in CMU, zxcvbn, and the techniques literature.
2. **Two estimation approaches** — Analytical (deterministic) for dictionary, rules, brute force; probabilistic (statistical) for Markov, PCFG, neural.
3. **Hash algorithm dominates** — MD5 to bcrypt cost=12 is ~114 million times slower; this must be a first-class simulator input.
4. **All reference tools are Python** — Confirms Python as the implementation language.
5. **External data requirements converge** — Frequency-ranked wordlists, keyboard graphs, rule files, and breach data are shared across multiple estimators.
6. **Password decomposition is the central problem** — Every tool centers on segmenting passwords into attackable components.

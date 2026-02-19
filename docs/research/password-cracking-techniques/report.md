# Password Cracking Techniques: Complete Catalog for Crack-Time Simulation

**Date:** 2026-02-15

## Executive Summary

This document catalogs every significant password cracking technique used by modern attackers and penetration testers, organized for implementation in a crack-time simulator that models all attacks running in parallel. The core insight for simulation is that real-world cracking is not a single technique -- it is an orchestrated pipeline where cheap, high-probability attacks run first and exhaustive searches serve as a last resort. A simulator modeling "time to crack" must account for the fact that a password falling to *any* technique in the pipeline is cracked, and the effective crack time is the minimum across all parallel attack channels.

The techniques below are ordered roughly by attack priority (how a professional would schedule them), not alphabetically.

---

## Table of Contents

1. [Credential Stuffing / Breach Lookup](#1-credential-stuffing--breach-lookup)
2. [Dictionary / Wordlist Attack](#2-dictionary--wordlist-attack)
3. [Rule-Based Attack](#3-rule-based-attack)
4. [Combinator Attack](#4-combinator-attack)
5. [Hybrid Attack](#5-hybrid-attack)
6. [Mask Attack](#6-mask-attack)
7. [Fingerprint / Policy-Aware Attack](#7-fingerprint--policy-aware-attack)
8. [Keyboard Walk Detection](#8-keyboard-walk-detection)
9. [PRINCE Attack](#9-prince-attack)
10. [Markov Chain Attack](#10-markov-chain-attack)
11. [PCFG (Probabilistic Context-Free Grammar)](#11-pcfg-probabilistic-context-free-grammar)
12. [Token-Based / Semantic Attack](#12-token-based--semantic-attack)
13. [Neural Network / ML Approaches](#13-neural-network--ml-approaches)
14. [Rainbow Tables](#14-rainbow-tables)
15. [Brute Force (Exhaustive Search)](#15-brute-force-exhaustive-search)
16. [Attack Scheduling and Priority Frameworks](#16-attack-scheduling-and-priority-frameworks)
17. [Hardware Throughput Reference](#17-hardware-throughput-reference)
18. [Simulator Design Implications](#18-simulator-design-implications)

---

## 1. Credential Stuffing / Breach Lookup

### Description
Direct lookup of a password hash against databases of previously breached passwords. If the exact password has appeared in any prior breach, this technique finds it instantly.

### Mechanism
1. Compile all known leaked passwords into a deduplicated list (or hash table for O(1) lookup)
2. Hash each candidate or look up the target hash directly
3. Match = cracked

### Effective Against
- Any password that has ever been used before and appeared in a breach
- Password reuse across services (extremely common -- studies show 60-70% of users reuse passwords)
- Simple, popular passwords ("123456", "password", "qwerty")

### Keyspace / Throughput
- **Keyspace:** ~1-2 billion unique passwords in major compilations (Collection #1 had 2.7B rows; HIBP Pwned Passwords has 600M+ unique passwords)
- **Throughput:** O(1) lookup per hash if using a hash table. Effectively instant for any match.
- **Coverage:** Catches an estimated 60-70% of consumer passwords in many populations

### Tools
- Have I Been Pwned Pwned Passwords API
- CrackStation lookup tables
- Custom hash tables built from breach compilations
- Hashcat in dictionary mode with breach-derived wordlists

### Simulator Modeling
Model as a **set membership test**. Given the target password, check if it exists in a set of N known breached passwords. Probability of match depends on the password's commonality and the breach database size. For simulation: assign a probability based on password frequency in known leaks. If the password is in the set, crack time = 0 (instant).

---

## 2. Dictionary / Wordlist Attack

### Description
Systematically hash every word in a wordlist and compare against the target hash. The wordlist may be a leaked password database, a natural-language dictionary, or a custom list built from OSINT.

### Mechanism
1. Load wordlist into memory
2. For each word: hash it (with the target's salt/algorithm) and compare to target hash
3. Match = cracked

### Effective Against
- Common passwords and dictionary words
- Passwords based on real words (names, places, pop culture references)
- Passwords reused from other services

### Keyspace / Throughput
- **Common wordlists:**
  - RockYou: ~14.3 million unique passwords
  - SecLists common passwords: 10K to 10M entries
  - Breach compilations: 100M to 1B+ entries
  - CeWL-generated site-specific lists: typically 1K-100K entries
- **Throughput:** Determined by hash algorithm speed. A single RTX 5090 processes:
  - MD5: 220.6 billion hashes/sec
  - bcrypt: 304,800 hashes/sec
  - 14M-word RockYou against MD5 completes in microseconds; against bcrypt, ~46 seconds

### Tools
- Hashcat (mode 0: Straight)
- John the Ripper (wordlist mode)
- Custom scripts

### Simulator Modeling
Model as **linear scan of a ranked probability list**. Wordlists are typically sorted by frequency. The crack time is the position of the password in the list divided by the hash rate. For simulation: if the password (or a base form of it) appears at rank R in a wordlist of size N, crack time = R / hash_rate.

---

## 3. Rule-Based Attack

### Description
Apply transformation rules to each word in a dictionary to generate variants. Rules perform operations like capitalization, appending digits, leet-speak substitution, character insertion/deletion, and case toggling. Hashcat's documentation calls this "the most flexible, accurate and efficient attack."

### Mechanism
1. Load a base wordlist
2. For each word, apply every rule in the rule file to generate transformed candidates
3. Hash each candidate and compare
4. Multiple rule files can be "stacked" -- their cross-product is applied (e.g., 64 rules x 50 rules = 3,200 rule combinations per base word)

### Rule Categories
| Category | Examples | What It Catches |
|----------|----------|-----------------|
| Capitalization | `c` (capitalize first), `u` (uppercase all), `T0-TN` (toggle position) | "password" -> "Password", "PASSWORD" |
| Appending | `$1`, `$!`, `$1$2$3` | "password" -> "password1", "password!" |
| Prepending | `^!`, `^1` | "password" -> "!password", "1password" |
| Leet speak | `sa4`, `se3`, `so0`, `si1` | "password" -> "p4ssw0rd" |
| Reversal | `r` | "password" -> "drowssap" |
| Duplication | `d` | "pass" -> "passpass" |
| Truncation | `]` (delete last), `[` (delete first) | Length trimming |
| Conditional | `>8` (reject if length > 8) | Policy compliance filtering |

### Key Rule Files
- **best64.rule**: 64 highest-yield rules. Standard first pass.
- **dive.rule**: ~99,000 rules sorted by effectiveness. Comprehensive but slow.
- **OneRuleToRuleThemAll**: Community-curated consolidated ruleset.
- **leetspeak.rule / Incisive-leetspeak.rule**: Leet substitutions.
- **toggles rules**: Case toggling at every position.

### Keyspace / Throughput
- **Multiplier effect:** candidates = wordlist_size x rule_count
  - RockYou (14M) x best64 (64 rules) = 915M candidates
  - RockYou x dive (99K rules) = 1.4 trillion candidates
  - Stacking best64 x leetspeak (64 x ~50) = ~3,200 rules x 14M = ~45 billion candidates
- **Throughput:** Same as dictionary attack per candidate (hash-rate limited)

### Tools
- Hashcat (mode 0 with `-r` flag)
- John the Ripper (mangling rules)

### Simulator Modeling
Model as **dictionary attack with a multiplier**. For each base word, generate N rule variants. The password is vulnerable if it matches any (base_word, rule_transform) pair. Key insight: most real passwords are a common base word + predictable transformation. Estimate the probability that a given password's "base form" exists in the dictionary, and the probability that the applied transformation is covered by a standard rule set.

---

## 4. Combinator Attack

### Description
Concatenate every word from one dictionary with every word from a second dictionary. Tests all two-word combinations.

### Mechanism
1. Load two wordlists ("left" and "right")
2. For each word in left: for each word in right: concatenate and hash
3. Order is NOT commutative -- "sunlight" comes from left="sun" + right="light", not the reverse (unless you swap dictionaries and run again)

### Effective Against
- Two-word passwords: "sunlight", "happybirthday", "iloveyou"
- Word + number combinations: "monkey123" (if numbers are in right list)
- Simple concatenation patterns

### Keyspace / Throughput
- **Keyspace:** |left| x |right|
  - Two 10K-word lists = 100M candidates
  - Two 100K-word lists = 10B candidates
- **Throughput:** Hash-rate limited, same as dictionary attack per candidate

### Tools
- Hashcat (mode 1: Combinator)
- John the Ripper (combinator mode)
- Hashcat's `combinator` utility for external preprocessing

### Simulator Modeling
Model as a **product space**. The password is vulnerable if it can be decomposed into word1 + word2 where both words appear in common dictionaries. Probability is the joint probability of both components being in the dictionary. For known dictionaries, this can be computed exactly.

---

## 5. Hybrid Attack

### Description
Combines a dictionary with a brute-force mask. One side provides dictionary words; the other side appends or prepends all combinations from a character-set mask.

### Mechanism
- **Mode 6 (Dictionary + Mask):** For each dictionary word, append all mask candidates. Example: "password" + `?d?d` tests "password00" through "password99".
- **Mode 7 (Mask + Dictionary):** Prepend mask candidates to each dictionary word. Example: `?d?d?d?d` + "password" tests "0000password" through "9999password".

### Effective Against
- Passwords that are a real word plus appended/prepended digits or symbols
- Policy-compliant passwords: "Summer2024!", "Pass1234"
- Extremely common pattern in corporate environments

### Keyspace / Throughput
- **Keyspace:** wordlist_size x mask_keyspace
  - 14M words x `?d?d` (100) = 1.4B candidates
  - 14M words x `?d?d?d?d` (10,000) = 140B candidates
  - 14M words x `?s?d?d` (330) = 4.6B candidates
- **Throughput:** Hash-rate limited per candidate

### Tools
- Hashcat (modes 6 and 7)
- John the Ripper (hybrid mode)

### Simulator Modeling
Model as **dictionary attack with suffix/prefix expansion**. Decompose the password into (base_word, appendage). Check if base_word is in a dictionary and if the appendage fits within common mask patterns. The crack time is the dictionary rank of the base word times the mask keyspace, divided by hash rate.

---

## 6. Mask Attack

### Description
Pattern-based brute force where each character position is constrained to a specific character set. More targeted than pure brute force because it exploits knowledge about password structure.

### Mechanism
1. Define a mask specifying the character set for each position
2. Enumerate all combinations matching the mask
3. Hash and compare each candidate

### Character Set Markers (Hashcat notation)
| Marker | Characters | Size |
|--------|-----------|------|
| `?l` | a-z | 26 |
| `?u` | A-Z | 26 |
| `?d` | 0-9 | 10 |
| `?s` | Special characters (space, punctuation) | 33 |
| `?a` | All printable ASCII | 95 |
| `?b` | All bytes (0x00-0xff) | 256 |

### Common Masks for Human Passwords
| Pattern | Mask | Keyspace | What It Targets |
|---------|------|----------|-----------------|
| `Ulllllldd` | `?u?l?l?l?l?l?l?d?d` | 26^6 x 10^2 = 30.9B | "Password12" |
| `Ulllldddd` | `?u?l?l?l?l?d?d?d?d` | 26^4 x 10^4 = 4.6B | "Word1234" |
| `llllllll` | `?l?l?l?l?l?l?l?l` | 26^8 = 208.8B | 8-char lowercase |
| `dddddddd` | `?d?d?d?d?d?d?d?d` | 10^8 = 100M | 8-digit PINs |

### Effective Against
- Passwords following predictable structural patterns
- Policy-compliant passwords with known composition rules
- Short passwords of any type

### Keyspace / Throughput
- **Keyspace:** Product of character set sizes at each position
- **Example:** 8-character full ASCII = 95^8 = 6.6 quadrillion candidates
- **At MD5 speed (1x RTX 5090, 220 GH/s):** 8-char full ASCII takes ~347 days
- **At bcrypt speed (1x RTX 5090, 305 kH/s):** 8-char full ASCII takes ~687 million years

### Tools
- Hashcat (mode 3: Brute-Force/Mask)
- Hashcat `.hcmask` files for mask lists
- John the Ripper (mask mode)

### Simulator Modeling
Model as **constrained exhaustive search**. Given a password, determine which mask(s) it matches and compute the keyspace of each mask. The crack time for a given mask is keyspace / hash_rate. If multiple masks are tried in sequence (via `.hcmask` files), model them as sequential phases with cumulative time. A password matching a small-keyspace mask is cracked faster.

---

## 7. Fingerprint / Policy-Aware Attack

### Description
Exploits knowledge of the target organization's password policy to constrain the search space. When policies require "minimum 8 characters, must include uppercase, lowercase, digit, and special character," users respond with highly predictable patterns.

### Mechanism
1. Identify the password policy (from documentation, error messages, or cracked password analysis)
2. Generate masks and rules targeting the most common policy-compliant patterns
3. Focus on the dominant patterns first (highest probability per guess)

### Common Policy-Driven Patterns
Users overwhelmingly place mandatory characters in predictable positions:
- **Uppercase:** Position 0 (first character) -- e.g., "Password"
- **Digit(s):** Appended at end -- "1", "12", "123", "2024", "2025"
- **Special character:** Very end -- "!", "@", "#", "$"
- **Archetypal password:** `Baseword` + `Digits` + `Special` = "Summer2024!"

### Effective Against
- Corporate/enterprise passwords under strict complexity policies
- Any environment where users satisfice (meet minimum requirements with minimum effort)
- Active Directory environments with typical Windows domain policies

### Keyspace / Throughput
- **Policy-aware mask for `Ulllldd!` pattern:** 26^4 x 10^2 x 33 = ~15M candidates (trivial)
- **Covering top 10 policy-compliant patterns for 8-12 char passwords:** typically 1B-100B candidates total
- This is orders of magnitude smaller than unconstrained search

### Tools
- Hashcat with custom masks derived from policy analysis
- PACK (Password Analysis and Cracking Kit) for analyzing cracked passwords and generating masks
- Hashcat's `--increment` flag for testing multiple lengths

### Simulator Modeling
Model as **policy-constrained mask search**. Given a known policy, generate the probability distribution of how users satisfy each constraint. Most users place uppercase first, digits at end, special at end. Weight the mask attempts by empirical frequency. NIST SP 800-63B (2024) now explicitly recommends against complexity requirements because they create these predictable patterns.

---

## 8. Keyboard Walk Detection

### Description
Targets passwords created by tracing patterns on the keyboard layout. These passwords appear random but are spatially predictable.

### Mechanism
1. Model the keyboard as a graph (keys = nodes, adjacency = edges)
2. Generate all walks of length N starting from each key, following directional routes (right, down-right, down-left, diagonal, etc.)
3. The candidate list covers all spatial patterns on the target keyboard layout

### Common Keyboard Walk Passwords
- "qwerty", "asdfgh", "zxcvbn" (horizontal walks)
- "qazwsx", "1qaz2wsx" (vertical/diagonal walks)
- "!QAZ2wsx" (shifted vertical walks meeting complexity requirements)
- Typically multiples of 4 characters in length (4, 8, 12, 16) due to memory chunking

### Effective Against
- Users who think keyboard patterns are "random"
- Passwords that appear to pass visual inspection for randomness
- Surprisingly common: "qwerty" appears over 1 million times in breach data

### Keyspace / Throughput
- **Keyspace:** For a standard QWERTY layout with 47 base keys and 4-8 directional routes:
  - 4-character walks: ~10,000-50,000 candidates
  - 8-character walks: ~100,000-1,000,000 candidates
  - 12-character walks: ~1-10 million candidates
- **Total keyspace is very small** -- the entire keyboard walk space can be exhausted in seconds even against bcrypt

### Tools
- Hashcat's **kwprocessor** (keyboard-walk generator with configurable keymaps and routes)
- SecLists pre-generated keyboard walk wordlists
- zxcvbn (password strength estimator that detects keyboard patterns client-side)

### Simulator Modeling
Model as a **graph traversal enumeration**. Build an adjacency graph of the keyboard layout. Enumerate all walks of relevant lengths. The password is vulnerable if it matches any walk. Since the total keyspace is small (thousands to low millions), this check is essentially free in a simulator -- it either matches or it doesn't, with near-zero time cost.

---

## 9. PRINCE Attack

### Description
PRINCE (PRobability INfinite Chained Elements) is an advanced word-combination generator that chains words from a single dictionary, ordered by probability. Unlike the standard combinator (which is limited to exactly two words), PRINCE chains 1 to N words.

### Mechanism
1. Load a single wordlist
2. Sort words by length and frequency
3. Generate all chains of 1, 2, 3, ... N words, ordered by total combined probability
4. Shorter/more frequent combinations come first (probability-ordered output)
5. Optionally pipe through hashcat's rule engine for further mutation

### Effective Against
- Multi-word passwords and passphrases: "letmein", "iloveyou", "correcthorsebatterystaple"
- Passwords formed by concatenating common words without separators
- Passphrase-style passwords that rely on length rather than complexity

### Keyspace / Throughput
- **Keyspace:** For a wordlist of W words with max chain length K:
  - 1-element chains: W candidates
  - 2-element chains: W^2 candidates
  - 3-element chains: W^3 candidates
  - Total: approximately W + W^2 + ... + W^K
  - With 10K words and K=3: ~1 trillion candidates
- **Probability ordering is the key advantage:** The most likely combinations are tested first, so the effective keyspace searched before finding human-chosen passwords is much smaller than the theoretical total

### Tools
- Hashcat's **princeprocessor** (standalone binary, pipes into hashcat)
- Combined with hashcat's `-g` flag for random rules (the "Purple Rain" attack)

### Simulator Modeling
Model as **probability-ordered multi-word combination search**. For a password decomposable into K common words, the crack position is approximately the product of each word's frequency rank. The Purple Rain variant adds a rule multiplier. For simulation: decompose the password into word components, look up each word's rank in a common wordlist, and compute the position in the probability-ordered output.

---

## 10. Markov Chain Attack

### Description
Statistical character-by-character password generation where each character is chosen based on the probability of it following the previous character at that position. Trained on real password datasets to learn which character sequences are most likely.

### Mechanism
1. **Training phase:** Analyze a corpus of known passwords to build a transition probability table. For each (position, previous_character) pair, record the probability distribution of the next character.
2. **Generation phase:** Starting from position 0, select characters in order of decreasing probability. At each position, the candidate set is ordered by P(char_i | char_{i-1}, position_i).
3. **Threshold control:** A configurable threshold limits how far into the probability tail to search, trading completeness for speed.

### Per-Position vs. Position-Independent
- **Hashcat (statsprocessor):** Per-position Markov chains -- considers both the previous character AND the current position. More accurate because password structure varies by position (e.g., capital letters are common at position 0, digits at the end).
- **John the Ripper (original):** Position-independent Markov chains -- considers only character transitions, not position. Less accurate but simpler.

### Effective Against
- Passwords that follow typical character-sequence patterns for their language/culture
- Passwords that "look like" common passwords but aren't exact dictionary entries
- Fills the gap between dictionary attacks (exact matches) and brute force (no statistical guidance)

### Keyspace / Throughput
- **With aggressive threshold:** Equivalent to ~10% of the full brute-force keyspace while catching ~80% of real passwords
- **With conservative threshold:** Approaches full brute-force keyspace but with better ordering
- **Throughput:** Same hash rate as brute force per candidate

### Tools
- Hashcat's **statsprocessor** (with **hcstatgen** for training)
- John the Ripper (Markov mode)
- OMEN (Ordered Markov ENumerator)

### Simulator Modeling
Model as **probability-weighted exhaustive search**. Compute the Markov probability of the target password given a standard training corpus. The password's rank in the Markov ordering determines when it would be reached. Higher-probability passwords (common character sequences) are found earlier. For simulation: given a training corpus, compute P(password) under the Markov model, then estimate its rank in the probability-ordered output.

---

## 11. PCFG (Probabilistic Context-Free Grammar)

### Description
Weir et al.'s (2009) approach that learns the structural grammar of passwords from training data. Passwords are parsed into typed segments (letters, digits, symbols), and a probabilistic grammar generates new candidates following the same structural patterns.

### Mechanism
1. **Parse training passwords** into segments by character type:
   - L (letters), D (digits), S (symbols)
   - Example: "Hello123!" -> L5 D3 S1
2. **Build grammar rules** with probabilities:
   - Structure: P(L5 D3 S1) = frequency of that pattern / total passwords
   - Terminals: P("Hello" | L5) = frequency of "Hello" among all 5-letter alpha segments
   - P("123" | D3) = frequency of "123" among all 3-digit segments
3. **Generate candidates** in descending probability order using the grammar

### Effective Against
- Passwords following common structural patterns (word + digits + symbol)
- Passwords that combine familiar components in predictable structures
- Outperforms dictionary + rules for structurally diverse password populations

### Performance
- Original Weir et al. experiments: cracked 28-129% more passwords than John the Ripper's default modes
- LPG-PCFG (2022): Improved variant that also targets low-probability passwords missed by standard PCFG

### Keyspace / Throughput
- **Keyspace:** Depends on training data richness and structural diversity
  - For a typical trained grammar: millions to billions of ordered candidates
  - The probability ordering means high-value candidates are generated first
- **Throughput:** Candidate generation is CPU-bound; hash computation is GPU-bound. The pipeline is usually hash-rate limited.

### Tools
- **pcfg_cracker** (Matt Weir's reference implementation on GitHub)
- Can pipe output into Hashcat for GPU-accelerated hashing
- John the Ripper has some PCFG-inspired functionality

### Simulator Modeling
Model as **grammar-based probability estimation**. Parse the target password into its L/D/S structure. Look up the probability of each structural element in a reference grammar trained on leaked passwords. The password's probability rank determines its position in the PCFG output queue. For simulation: compute P(password) = P(structure) x Product(P(terminal_i | type_i, length_i)). The crack time is the rank corresponding to that probability divided by hash rate.

---

## 12. Token-Based / Semantic Attack

### Description
Extends PCFG with linguistic analysis. Passwords are segmented into semantically meaningful tokens (names, dates, words, keyboard patterns, leet-speak substitutions) rather than just character-type segments. This captures higher-level structure that pure character analysis misses.

### Mechanism
1. **Tokenization:** Decompose the password into semantic units using NLP:
   - Base words (dictionary words, names)
   - Date patterns (MMDDYYYY, birth years)
   - Digit sequences (PIN-like, sequential)
   - Leet-speak transformations
   - Keyboard walk fragments
   - Special character padding
2. **Semantic classification:** Assign part-of-speech or category tags to each token
3. **Grammar generation:** Build a probabilistic grammar over token types, with probability distributions for each token category
4. **Candidate generation:** Generate passwords by sampling token sequences ordered by joint probability

### Research Highlights
- Veras et al. (NDSS 2014): First semantic password analysis framework. Demonstrated that semantic grammars outperform standard PCFG.
- ACM TOPS large-scale analysis: Part-of-speech (syntactic) patterns are more consequential to security than semantic categories. ~5% of passwords are pure date patterns.
- PassTSL (2024): Two-stage learning model operating at token level rather than character level.

### Effective Against
- Passwords built from personal information (names, birthdays, pet names)
- Culturally-patterned passwords (favorite sports teams, movie references)
- Passwords that are meaningful phrases or sentences

### Keyspace / Throughput
- **Highly variable:** Depends on the token vocabulary and grammar complexity
- **Typically smaller effective keyspace** than character-level approaches because semantic constraints reduce the search space
- **Throughput:** CPU-limited candidate generation, GPU-limited hashing

### Tools
- Research prototypes (Veras et al., PassTSL)
- pcfg_cracker with extended grammars
- Custom implementations combining NLP tokenization with PCFG frameworks

### Simulator Modeling
Model as **semantic decomposition with probability lookup**. For each token in the password, compute its probability given its semantic category and position. The overall password probability is the product of structural probability and individual token probabilities. This gives a finer-grained estimate than PCFG alone. For common semantic patterns (name + year + "!"), the effective keyspace can be very small.

---

## 13. Neural Network / ML Approaches

### Description
Machine learning models trained on leaked password datasets to generate new password guesses. Multiple architectures have been explored: GANs, LSTMs, variational autoencoders, and hybrid models.

### Key Models

#### PassGAN (2017)
- **Architecture:** Improved Wasserstein GAN (IWGAN) with residual blocks and 1D convolutions
- **Training:** ~80% of RockYou dataset; discriminator learns real vs. generated passwords
- **Performance:** 47% match rate on held-out test set
- **Strength:** Learns implicit password patterns without explicit rule engineering
- **Weakness:** No guaranteed probability ordering; generates duplicates; slow training

#### G-Pass (2022)
- **Architecture:** LSTM generator + multi-filter-size CNN discriminator with Gumbel-Softmax
- **Improvement over PassGAN:** Higher quality samples, better cracking rate

#### GENPass
- **Architecture:** Hybrid PCFG + LSTM -- uses PCFG structure for grammar and LSTM for terminal generation
- **Combines** the structural awareness of PCFG with the generative power of neural networks

#### LLMs / Transformers (2025 research)
- A 2025 empirical study found that large language models **struggle with password cracking** tasks
- Transformer models are not yet competitive with traditional methods (PCFG, Markov, rules) for this specific application
- The password domain's statistical properties differ from natural language in ways that confuse LLMs

### Effective Against
- Passwords following implicit patterns not captured by explicit rules
- Novel password structures that rules and PCFG grammars haven't been designed for
- Best as a **complement** to traditional methods, catching what they miss

### Keyspace / Throughput
- **Generation speed:** GPU-dependent, but much slower than hash computation. The bottleneck is candidate generation, not hashing.
- **No probability ordering guarantee:** Generated candidates are not strictly ordered by likelihood, reducing efficiency compared to PCFG/Markov
- **Typical deployment:** Generate a large candidate list offline, then use as a wordlist for hashcat

### Tools
- PassGAN (GitHub: brannondorsey/PassGAN)
- Research implementations for G-Pass, GENPass
- Custom LSTM/transformer training scripts

### Simulator Modeling
Model neural approaches as an **additional probability coverage layer**. They catch passwords that fall through the cracks of dictionary, rules, PCFG, and Markov attacks. For simulation: estimate a "neural coverage probability" -- the likelihood that the password matches the distribution learned by a neural model but wasn't already covered by earlier attacks. This is inherently approximate and represents the incremental coverage beyond traditional methods.

---

## 14. Rainbow Tables

### Description
Pre-computed tables that store compressed hash-to-plaintext mappings using a chain structure. A classic space-time tradeoff: more storage means less computation at crack time.

### Mechanism
1. **Chain construction:** Starting from a plaintext, hash it, apply a "reduction function" to get another plaintext, hash that, repeat for K steps. Store only the first and last values of each chain.
2. **Lookup:** Given a target hash, apply the reduction function at each chain position until finding a stored endpoint. Then replay from the corresponding start point to find the matching plaintext.
3. **Multiple reduction functions** (one per chain position) prevent collisions -- this is the "rainbow" part.

### Effective Against
- **Unsalted hashes only** -- a unique salt per password makes rainbow tables impractical
- Legacy systems: LM hashes, unsalted MD5, unsalted SHA1
- NTLM hashes (notably still unsalted in Windows environments)

### Keyspace / Throughput
- **Space:** Tables for useful keyspaces range from hundreds of GB to multiple TB
- **Lookup time:** Seconds to minutes per hash (much faster than brute force, much slower than hash table lookup)
- **Pre-computation time:** Days to weeks for comprehensive tables; done once, used many times

### Tools
- RainbowCrack (rtgen, rtsort, rcrack)
- Ophcrack (specifically for Windows LM/NTLM hashes)
- CrackStation (online service with pre-built tables)

### Simulator Modeling
Model as a **conditional instant-crack test**. If the hash algorithm is unsalted AND rainbow tables exist for the target keyspace, then any password within that keyspace is cracked in near-zero time. If the hash is salted, rainbow tables provide zero benefit. For simulation: check (is_salted, keyspace_coverage). If both conditions met, crack time = table_lookup_time (seconds). Otherwise, not applicable.

---

## 15. Brute Force (Exhaustive Search)

### Description
Try every possible combination of characters up to a given length. The ultimate fallback -- guaranteed to find the password eventually, but the time grows exponentially with length and character-set size.

### Mechanism
1. Select a character set (digits, lowercase, mixed case, full ASCII)
2. Starting from length 1, enumerate all combinations
3. Hash each candidate and compare

### Keyspace by Length and Character Set

| Length | Digits (10) | Lower (26) | Mixed (52) | Full ASCII (95) |
|--------|------------|------------|------------|-----------------|
| 6 | 1M | 309M | 19.8B | 735B |
| 8 | 100M | 208.8B | 53.5T | 6.6Q |
| 10 | 10B | 141.2T | 144.6Q | 59.9 Quintillion |
| 12 | 1T | 95.4Q | 390.9Q | 540 Sextillion |

### Effective Against
- Short passwords (6 characters or fewer are trivial regardless of composition)
- Truly random passwords (no pattern-based shortcut exists)
- When all other techniques have been exhausted

### Throughput Reference (Single RTX 5090)

| Algorithm | Hash Rate | 8-char Full ASCII Time |
|-----------|-----------|----------------------|
| MD5 | 220.6 GH/s | ~8.3 hours |
| SHA1 | 70.2 GH/s | ~26 hours |
| SHA256 | 28.4 GH/s | ~2.7 days |
| NTLM | 340.1 GH/s | ~5.4 hours |
| bcrypt | 304.8 kH/s | ~687 million years |

### Hive Systems 2025 Benchmarks (12x RTX 5090, bcrypt w/factor 10)
| Composition | 8-char | 12-char |
|-------------|--------|---------|
| Numbers only | 15 min | ~25 hours |
| Lowercase only | 3 weeks | ~200 years |
| Alpha + numbers | 62 years | ~30K years |
| Full complexity | 164 years | ~3,000 years |

### Tools
- Hashcat (mode 3 with full charset mask)
- John the Ripper (incremental mode)

### Simulator Modeling
Model as **keyspace_size / hash_rate = time**. The keyspace is the product of character-set sizes at each position. For a truly random password of length L from character set C: time = C^L / hash_rate. This is the absolute worst case for the attacker and the theoretical upper bound for crack time. Critical note: this calculation assumes the password is truly random. Human-chosen passwords almost never require full brute force because earlier techniques catch them first.

---

## 16. Attack Scheduling and Priority Frameworks

### Professional Attack Ordering

Based on penetration testing methodology and DEF CON Crack Me If You Can competition strategies, the standard attack priority is:

#### Phase 1: Instant Checks (seconds)
1. **Breach database lookup** -- check against known leaked passwords
2. **Keyboard walk wordlist** -- small keyspace, instant exhaust
3. **Top 1000/10000 most common passwords** -- trivial dictionary check

#### Phase 2: Quick Wins (minutes to hours)
4. **Dictionary attack + best64 rules** -- highest ROI attack
5. **Dictionary + comprehensive rules** (dive.rule, OneRuleToRuleThemAll)
6. **Combinator attack** with common word pairs
7. **Hybrid attack** -- dictionary + short mask (1-3 appended chars)

#### Phase 3: Targeted Attacks (hours to days)
8. **Policy-aware mask attacks** -- based on observed patterns from Phase 2 cracks
9. **PRINCE attack** -- multi-word combinations
10. **PCFG-generated candidates** -- structurally diverse guesses
11. **Markov chain candidates** -- probability-ordered character sequences
12. **Hybrid attack** -- dictionary + longer masks (4+ appended chars)

#### Phase 4: Exhaustive (days to never)
13. **Neural/ML-generated candidates** -- incremental coverage
14. **Mask attack** -- common patterns, incrementing length
15. **Full brute force** -- last resort, only viable for short passwords

### Feedback Loop
After each phase, analyze newly cracked passwords to:
- Discover the organization's password policy
- Identify common base words and patterns
- Generate targeted masks and rules for subsequent phases
- Feed cracked passwords back as dictionary entries

### Automation Tools
- **Hashcatalyst (2025):** Automates multi-stage hashcat workflow orchestration
- **hate_crack (TrustedSec):** Automated password cracking pipeline
- **PACK:** Password Analysis and Cracking Kit for mask/rule generation from cracked passwords

### DEF CON Crack Me If You Can
- KoreLogic's annual 48-hour competition
- Split into PRO and STREET tiers
- Yearly twists: international passwords, bcrypt-only, password rotation, case sensitivity
- Winning teams use all techniques above in parallel, with custom tooling for orchestration
- Key competitive advantage: fast iteration on the feedback loop (crack some -> analyze -> generate targeted attacks)

---

## 17. Hardware Throughput Reference

### Single GPU Benchmarks (Hashcat)

| Algorithm | RTX 5090 | RTX 4090 | Ratio |
|-----------|----------|----------|-------|
| MD5 | 220.6 GH/s | 164.1 GH/s | 1.34x |
| NTLM | 340.1 GH/s | 288.5 GH/s | 1.18x |
| SHA1 | 70.2 GH/s | 50.6 GH/s | 1.39x |
| SHA256 | 28.4 GH/s | 22.0 GH/s | 1.29x |
| SHA512 | 10.0 GH/s | 7.5 GH/s | 1.33x |
| bcrypt (w=5) | 304.8 kH/s | 184 kH/s | 1.66x |
| scrypt | 7,760 H/s | 7,126 H/s | 1.09x |
| WPA-PBKDF2 | 3.4 MH/s | 2.5 MH/s | 1.36x |

### Multi-GPU Scaling
- Performance scales roughly linearly with GPU count
- 12x RTX 5090 = ~12x single-GPU performance (with some overhead)
- Cloud instances (e.g., 8x A100 or 8x H100) provide alternative scaling paths
- Hive Systems 2025 uses 12x RTX 5090 as its reference "high-end consumer" setup

### Hash Algorithm Impact
The hash algorithm is the single biggest variable in crack time:
- **Fast hashes (MD5, NTLM, SHA1):** Designed for speed, not password storage. Billions of hashes/sec per GPU.
- **Slow hashes (bcrypt, scrypt, Argon2):** Deliberately expensive. Thousands to hundreds of thousands per GPU.
- **The ratio between MD5 and bcrypt is ~700,000x on the same hardware.** A password that takes 1 second to brute-force against MD5 takes ~8 days against bcrypt (work factor 5) or ~22 years against bcrypt (work factor 12).

---

## 18. Simulator Design Implications

### Core Architecture: Parallel Attack Model

A crack-time simulator should model all applicable attacks running in parallel. The effective crack time is:

```
crack_time = MIN(time_breach_lookup, time_dictionary, time_rules, time_hybrid,
                 time_mask, time_prince, time_pcfg, time_markov, time_brute_force, ...)
```

### For Each Attack, the Simulator Needs

1. **Applicability check:** Does this attack apply to the given password?
   - Breach lookup: Is the password in the breach database?
   - Keyboard walk: Does the password match a spatial pattern?
   - Rainbow table: Is the hash unsalted?

2. **Position/rank estimation:** Where does this password fall in the attack's output ordering?
   - Dictionary: What rank is the password (or its base form) in the wordlist?
   - Rules: Is the password = base_word + known_transformation?
   - PCFG: What's the grammar probability?
   - Markov: What's the character-sequence probability?

3. **Time calculation:** position / hash_rate = time

### Suggested Password Decomposition Pipeline

For a given input password, the simulator should:

1. **Check breach databases** -- instant match or not
2. **Detect keyboard walks** -- spatial pattern matching
3. **Tokenize into semantic components:**
   - Identify base word(s) via dictionary lookup
   - Identify digit patterns (years, sequences, PINs)
   - Identify leet-speak substitutions
   - Identify special character padding
4. **For each identified structure, compute attack times:**
   - Dictionary rank of base word x rule multiplier / hash_rate
   - PCFG probability rank / hash_rate
   - Mask keyspace / hash_rate
   - Hybrid: dictionary_rank x mask_keyspace / hash_rate
5. **Return the minimum time across all attacks**

### Key Variables the Simulator Must Accept
- **Hash algorithm:** Determines hash rate (MD5 vs bcrypt changes results by 6 orders of magnitude)
- **Hardware configuration:** Number and type of GPUs
- **Wordlist/breach database scope:** What dictionaries are assumed available
- **Password policy (optional):** Constrains the mask/fingerprint attacks
- **Attacker sophistication level:** Determines which techniques are used (script kiddie vs. professional vs. nation-state)

### Modeling Probabilities vs. Certainties

Some techniques give deterministic results (breach lookup, keyboard walk, brute force), while others are probabilistic (PCFG rank, Markov rank, neural coverage). The simulator should:
- Use **deterministic checks** where possible (is this exact password in the dictionary?)
- Use **probability estimates** where exact computation is impractical (what's the Markov probability of this character sequence?)
- Use **brute force as the upper bound** -- every password has a deterministic brute-force crack time

---

## Sources

All sources are documented with full citations in the companion file `background.md`. Key references include:

- Hashcat wiki and tool documentation (hashcat.net)
- Weir et al., "Password Cracking Using Probabilistic Context-Free Grammars" (IEEE S&P 2009)
- Hitaj et al., "PassGAN: A Deep Learning Approach for Password Guessing" (2017)
- Veras et al., "On the Semantic Patterns of Passwords" (NDSS 2014)
- Hive Systems 2025 Password Table (hivesystems.com)
- NIST SP 800-63B (2024 revision) on password guidelines
- RTX 5090/4090 hashcat benchmarks (Chick3nman, GitHub Gists)
- KoreLogic Crack Me If You Can competition archives
- TCM Security, TrustedSec, and NotSoSecure professional cracking guides

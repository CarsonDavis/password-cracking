# Requirements Specification

Formal functional and non-functional requirements for the Password Crack-Time Simulator, derived from the [project overview](01-project-overview.md), [research findings](research/), and original [project definition](../PROJECT.md).

---

## Functional Requirements

### Input Handling

| ID | Requirement | Source | Priority |
|----|------------|--------|----------|
| FR-001 | Accept a single password string as input | PROJECT.md | Must |
| FR-002 | Accept a hash algorithm parameter (MD5, SHA-256, bcrypt with configurable cost, scrypt, Argon2id, NTLM, PBKDF2) | PROJECT.md lines 77-81 | Must |
| FR-003 | Accept a hardware tier/profile parameter (single GPU through nation-state) | PROJECT.md lines 92-95 | Must |
| FR-004 | Accept a batch file of passwords for bulk evaluation | PROJECT.md | Should |
| FR-005 | Accept optional user context (username, email, site name, birthdate) for targeted attack simulation | PROJECT.md | Should |
| FR-006 | Accept optional attacker profile presets (script kiddie, competent, professional, nation-state) | PROJECT.md lines 92-95 | Should |

### Attack Estimators

| ID | Requirement | Source | Priority |
|----|------------|--------|----------|
| FR-007 | Estimate brute-force crack time as `charset^length / hash_rate` | Research: all tools | Must |
| FR-008 | Estimate dictionary attack crack time using frequency-ranked wordlist position | Research: zxcvbn | Must |
| FR-009 | Estimate keyboard walk attack time using spatial adjacency graph formula | Research: zxcvbn | Must |
| FR-010 | Estimate date pattern attack time from year-space and date format variations | Research: zxcvbn | Must |
| FR-011 | Estimate character sequence attack time for constant-delta sequences | Research: zxcvbn | Must |
| FR-012 | Estimate repeat pattern attack time as `base_guesses * repeat_count` | Research: zxcvbn | Must |
| FR-013 | Estimate mask attack time from per-position character class keyspace | Research: techniques catalog | Must |
| FR-014 | Estimate rule-based attack time via rule inversion (best64.rule minimum) | Research: UChicago | Must |
| FR-015 | Estimate combinator attack time from two-word dictionary split | Research: techniques catalog | Must |
| FR-016 | Estimate hybrid attack time from dictionary word + mask suffix/prefix | Research: techniques catalog | Must |
| FR-017 | Estimate PCFG attack time via grammar probability and precomputed lookup table | Research: PCFG cracker | Must |
| FR-018 | Estimate Markov/OMEN attack time via level-based probability discretization | Research: OMEN | Must |
| FR-019 | Estimate breach lookup result via set membership test | Research: HIBP | Should |
| FR-020 | Estimate PRINCE multi-word attack time from word frequency product | Research: techniques catalog | Should |
| FR-021 | Estimate neural network attack time via Monte Carlo CDF estimation | Research: CMU neural | Could |

### Core Engine

| ID | Requirement | Source | Priority |
|----|------------|--------|----------|
| FR-022 | Implement DP decomposition engine that finds minimum-cost non-overlapping password segmentation across all estimators | Research: zxcvbn | Must |
| FR-023 | Compute final crack time as `min(all_strategy_times)` (min-auto ensemble) | Research: CMU, validated across all tools | Must |
| FR-024 | Convert guess numbers to wall-clock time using configurable hardware hash rates | Research: benchmarks | Must |
| FR-025 | Detect and handle l33t-speak substitutions with binomial variation counting | Research: zxcvbn | Must |
| FR-026 | Detect uppercase variations with appropriate multiplier formulas | Research: zxcvbn | Must |
| FR-038 | Detect reversed dictionary words (e.g., "drowssap" matches "password" reversed) and apply a 2x multiplier to the base rank | Research: zxcvbn | Should |
| FR-039 | Define attacker profile presets specifying which estimators to run, which hardware tier to use, and which data assets to load. Minimum profiles: script_kiddie (Phase 1 estimators, consumer hardware), professional (all estimators, large_rig hardware), nation_state (all estimators, nation_state hardware) | PROJECT.md lines 94-97 | Should |

### Output

| ID | Requirement | Source | Priority |
|----|------------|--------|----------|
| FR-027 | Report crack time in human-readable units (seconds through years) | PROJECT.md | Must |
| FR-028 | Report winning attack strategy (which technique cracks fastest) | PROJECT.md | Must |
| FR-029 | Report per-strategy breakdown with individual guess numbers and times | PROJECT.md | Must |
| FR-030 | Report categorical strength rating (0-4 scale) | Research: zxcvbn | Must |
| FR-031 | Report human-readable explanation of the weakest decomposition | PROJECT.md | Should |
| FR-032 | Support JSON output format for programmatic consumption | PROJECT.md | Must |
| FR-033 | Support human-readable CLI output format | PROJECT.md | Must |

### Data Management

| ID | Requirement | Source | Priority |
|----|------------|--------|----------|
| FR-034 | Bundle default frequency-ranked wordlists (~30K common passwords, English words, names) | Research: zxcvbn data | Must |
| FR-035 | Bundle keyboard adjacency graphs (QWERTY, Dvorak, keypad) | Research: zxcvbn data | Must |
| FR-036 | Bundle hash rate benchmark data as JSON lookup table | Research: benchmarks report | Must |
| FR-037 | Provide download script for optional large assets (RockYou, PCFG grammar, Markov tables, breach Bloom filter) | Research: data requirements | Should |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-001 | Single-password evaluation latency (Phase 1 estimators) | < 500 ms | Interactive CLI use |
| NFR-002 | Single-password evaluation latency (all estimators) | < 2 seconds | Acceptable for comprehensive analysis |
| NFR-003 | Batch evaluation throughput | > 100 passwords/sec (Phase 1 estimators) | Practical for password audits |

### Accuracy

| ID | Requirement | Target | Validation |
|----|------------|--------|------------|
| NFR-004 | Brute-force estimator vs. Hive Systems tables | Within 2x | Known keyspace / known hash rate |
| NFR-005 | Dictionary estimator rank accuracy | Exact match against wordlist position | Direct verification |
| NFR-006 | Rule-based estimator vs. actual Hashcat positions | Within 10x | Ground-truth Hashcat runs |
| NFR-007 | PCFG estimator vs. pcfg_guesser.py | Within 10x | Reference tool comparison |
| NFR-008 | Markov estimator vs. OMEN level assignment | Within 1-2 orders of magnitude | Reference tool comparison |
| NFR-009 | Overall estimate vs. zxcvbn | Less than or equal to zxcvbn | We model more attacks, should find faster paths |

### Portability

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-010 | Python version compatibility | Python 3.10+ | Modern type syntax; broad support |
| NFR-011 | Core dependency count | stdlib + numpy only | Easy install; no heavy ML deps |
| NFR-012 | Installation method | pip-installable via pyproject.toml | Standard Python packaging |

### Data Footprint

| ID | Requirement | Target | Rationale |
|----|------------|--------|-----------|
| NFR-013 | Bundled data size (Phase 1) | < 5 MB | Lightweight default install |
| NFR-014 | Full data size with optional downloads | < 2 GB | Practical disk usage |

### Extensibility

| ID | Requirement | Description |
|----|------------|-------------|
| NFR-015 | Adding a new estimator requires adding one file (no core modifications) | Plugin-style estimator architecture |
| NFR-016 | Hash rate data is configurable (not hardcoded) | JSON lookup table, user-overridable |
| NFR-017 | Strength rating thresholds are configurable | Allow hash-algorithm-aware thresholds |

---

## Acceptance Criteria

### Per Functional Requirement

| FR | Acceptance Criterion |
|----|---------------------|
| FR-001 | `crack-time estimate "password123"` returns valid output |
| FR-002 | `--hash bcrypt_cost12` uses bcrypt cost=12 hash rate (1,437 H/s baseline) |
| FR-003 | `--hardware rig_8x_rtx4090` applies 7.0x multiplier to base rate |
| FR-007 | `8j$kL2!nQ` (10 random chars, full ASCII) returns brute-force estimate of 95^10 guesses |
| FR-008 | `password` returns dictionary rank 1-2 (depending on wordlist) |
| FR-009 | `qwerty` is detected as keyboard walk on QWERTY graph |
| FR-010 | `01151987` is detected as date (January 15, 1987) |
| FR-013 | `?u?l?l?l?l?l?d?d?d?d?s` mask produces 26 * 26^5 * 10^4 * 33 keyspace |
| FR-014 | `P@ssw0rd!` is found via rule inversion as "password" + l33t + append rules |
| FR-015 | `sunlight` is split as "sun" + "light" with combinator rank calculation |
| FR-022 | `p@ssword123` decomposes optimally as ["p@ssword" (dict+l33t)] + ["123" (sequence)] |
| FR-023 | For every test password, final crack time = min of all individual strategy times |
| FR-027 | Crack times displayed as "< 1 second", "3.2 hours", "47 years", etc. |
| FR-030 | Strength ratings 0-4 match thresholds defined in [validation strategy](08-validation-strategy.md) |

### System-Level Acceptance

| Criterion | Test |
|-----------|------|
| All 21 test passwords from [validation strategy](08-validation-strategy.md) produce the expected winning attack | Integration test suite |
| Our estimate is ≤ zxcvbn's estimate for all test passwords | Comparison test suite |
| Brute-force estimates match Hive Systems within 2x for random passwords | Benchmark comparison |
| Full pipeline runs on 1,000 passwords in < 10 seconds (Phase 1 estimators) | Performance test |

---

See also: [Use Cases](03-use-cases.md) | [Architecture](04-architecture.md) | [Validation Strategy](08-validation-strategy.md)

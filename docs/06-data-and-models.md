# External Data & Model Requirements

The simulator relies on several external data assets shared across multiple estimators. This document catalogs all required data, their sources, sizes, and licensing considerations.

---

## Data Asset Inventory

| Asset | Source | Approx. Size | Purpose | Phase |
|-------|--------|-------------|---------|-------|
| Frequency-ranked wordlist (common passwords) | RockYou / SecLists | ~14.3M entries, ~150 MB | Dictionary attack, PCFG/Markov training | 1 |
| English word frequency list | Wikipedia corpus | 30K entries, ~300 KB | Dictionary matching | 1 |
| Name/surname frequency lists | US Census / zxcvbn data | ~15K entries, ~200 KB | Personal info detection | 1 |
| Keyboard adjacency graphs | zxcvbn source | ~10 KB per layout | Keyboard walk detection + estimation | 1 |
| Hashcat rule files (best64, dive) | Hashcat distribution | 64 + 99K rules, ~2 MB | Rule inversion estimator | 2 |
| Hash rate benchmark table | Our benchmarks report | ~5 KB JSON | Hardware calculator | 1 |
| PCFG trained grammar | pcfg_cracker output | 10--100 MB | PCFG probability computation | 2 |
| PCFG probability-to-rank lookup table | Precomputed from generator | ~10 MB | PCFG guess number estimation | 2 |
| OMEN n-gram tables | OMEN createNG output | ~50 MB | Markov probability + level estimation | 2 |
| Breach password Bloom filter | HIBP Pwned Passwords | ~1 GB (600M+ passwords) | Breach lookup estimator | 2 |
| L33t substitution table | zxcvbn source | ~1 KB | L33t detection + variation counting | 1 |
| Mask pattern library | PACK analysis / Hive tables | ~10 KB | Common mask patterns for mask estimator | 1 |
| Neural network model (optional) | Train on password data | 10--50 MB | Neural estimator | 4 |
| Monte Carlo sample CDF (optional) | Precomputed from neural model | ~100 MB | Neural guess number estimation | 4 |

## Shared Data Across Estimators

Several assets are shared. One set of frequency-ranked wordlists serves the dictionary estimator, the combinator estimator, and as training data for PCFG/Markov models. The keyboard adjacency graphs are reused by both the keyboard walk estimator and the PCFG parser's walk detector.

| Asset | Used By |
|-------|---------|
| Frequency-ranked wordlists (RockYou, etc.) | Dictionary attack, PCFG training, combinator, hybrid, zxcvbn |
| Keyboard adjacency graphs | zxcvbn keyboard walk, PCFG Cracker walk detection |
| Hashcat/JtR rule files (best64, dive) | UChicago analytic rule inversion, rule-based attacks |
| Breach password compilations | Breach lookup, training data for all models |
| Name/surname frequency lists | zxcvbn dictionary matching, semantic analysis |
| PCFG-trained grammar tables | PCFG estimator probability computation |
| Markov n-gram tables | OMEN/Markov estimator level computation |
| Hashcat benchmark data | Hardware calculator hash rates |

## Data Licensing & Ethical Considerations

- **RockYou wordlist**: Leaked in 2009; widely used in academic research. Contains real user passwords. Acceptable for research use; do not redistribute with personally identifiable information.
- **HIBP Pwned Passwords**: Available under creative commons license via k-anonymity API or downloadable hash sets. Hashes only (SHA-1), no plaintext redistribution.
- **SecLists**: MIT-licensed collection of security assessment wordlists.
- **Hashcat rule files**: Distributed with Hashcat under MIT license.
- **zxcvbn data**: MIT-licensed frequency lists and adjacency graphs.
- **US Census name data**: Public domain (US government).
- **PCFG/Markov trained models**: Models trained on password data may indirectly encode leaked passwords. Distribute model parameters, not training data.

## Acquisition Instructions

### Bundled with the simulator (Phase 1)
- zxcvbn frequency lists (~30K common passwords, ~30K English words, names/surnames)
- Keyboard adjacency graphs (QWERTY, Dvorak, keypad)
- L33t substitution table
- Hash rate benchmark table (JSON, from [benchmarks report](research/password-cracking-benchmarks/report.md))
- Mask pattern library

### Downloadable via script (Phase 2+)
- RockYou full wordlist (14.3M entries)
- Hashcat rule files (best64.rule, dive.rule)
- PCFG trained grammar (from pcfg_cracker)
- OMEN n-gram tables (from OMEN createNG)
- HIBP Pwned Passwords Bloom filter

### Precomputed by user (Phase 2+)
- PCFG probability-to-rank lookup table (run generator, sample pairs)
- Monte Carlo sample CDF (for neural estimator)

## Data Format Specifications

### Keyboard Adjacency Graphs (JSON)

One JSON file per layout. Each key maps to a list of neighbors (null = no neighbor in that direction). Directions are: [right, upper-right, upper-left, left, lower-left, lower-right] for standard keys. Shifted variants of a key share the same adjacency.

```json
// data/keyboards/qwerty.json
{
  "q": ["w", null, null, null, null, "a"],
  "w": ["e", null, null, "q", "a", "s"],
  "a": ["s", "w", "q", null, null, "z"],
  "1": ["2", null, null, "`", null, "q"],
  ...
}
```

**Derived constants** (computed at load time):
- `starting_positions` = number of keys in the graph (QWERTY: 47, keypad: 15)
- `avg_degree` = mean number of non-null neighbors per key (QWERTY: 4.595, keypad: 5.066)

Source: zxcvbn's `adjacency_graphs.coffee`, converted to JSON. Three layouts: `qwerty.json`, `dvorak.json`, `keypad.json`.

### L33t Substitution Table (JSON)

Maps each original letter to a list of possible l33t substitutions. Used in both directions: detection (l33t→original) and variation counting.

```json
// data/l33t_table.json
{
  "a": ["@", "4"],
  "b": ["8"],
  "c": ["(", "{", "["],
  "e": ["3"],
  "g": ["6", "9"],
  "i": ["1", "!", "|"],
  "l": ["1", "|"],
  "o": ["0"],
  "s": ["$", "5"],
  "t": ["7", "+"],
  "x": ["%"],
  "z": ["2"]
}
```

During detection, this is inverted: for each character in the password, check if it appears as a l33t value; if so, record the possible original(s). Then enumerate de-l33t variants (capped at 2^10 = 1024) and check each against dictionaries.

### Mask Pattern Library (JSON)

Common structural patterns observed in real password sets (from PACK analysis of breach data). Used by the mask estimator as a reference for how attackers prioritize masks.

```json
// data/masks/common_masks.json
[
  {"mask": "?l?l?l?l?l?l",       "frequency": 0.082, "keyspace": 308915776},
  {"mask": "?l?l?l?l?l?l?l?l",   "frequency": 0.071, "keyspace": 208827064576},
  {"mask": "?l?l?l?l?l?l?d?d",   "frequency": 0.054, "keyspace": 3089157760},
  {"mask": "?u?l?l?l?l?l?d?d",   "frequency": 0.041, "keyspace": 3089157760},
  {"mask": "?l?l?l?l?l?l?l?l?d?d", "frequency": 0.033, "keyspace": 20882706457600},
  {"mask": "?u?l?l?l?l?l?l?d?d?d?d", "frequency": 0.028, "keyspace": 802857254400}
]
```

The mask estimator computes the password's actual mask from character classes, then looks it up in this library. If found, the keyspace is the product of per-position class sizes. If not in the library, the mask estimator still computes the keyspace — the library just helps with ranking/prioritization.

### Frequency-Ranked Wordlists (TSV)

One word per line, sorted by frequency rank (most common first). Rank is the 1-based line number.

```
// data/wordlists/common_passwords.tsv
password
123456
12345678
qwerty
abc123
monkey
...
```

Loaded into two data structures at startup:
- `word_to_rank: dict[str, int]` — O(1) rank lookup
- `word_set: set[str]` — O(1) membership test

Multiple wordlists are loaded with different dictionary names: `common_passwords`, `english`, `names`, `surnames`.

## Local Data: analytic-password-cracking

The [analytic-password-cracking](../../analytic-password-cracking/) directory at the project root contains a clone of the UChicago analytic password cracking tool. This is an external repository with its own `.git` history, kept at the top level for direct reference during development.

---

See also: [Architecture](04-architecture.md) | [Estimator Specs](05-estimator-specs.md) | [Implementation Roadmap](07-implementation-roadmap.md)

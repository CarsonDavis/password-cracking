# System Architecture

High-level architecture of the Password Crack-Time Simulator, including the pipeline design, technology choices, shared analysis layer, and package structure.

---

## Architecture Overview

```
                        ┌──────────────────────┐
                        │    CLI / API Entry    │
                        │  password, hash_algo, │
                        │  hardware_tier        │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Password Analyzer   │
                        │  (shared analysis)    │
                        │  - tokenize           │
                        │  - detect patterns    │
                        │  - compute properties │
                        └──────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼─────────┐ ┌───────▼────────┐ ┌────────▼────────┐
    │ Analytical         │ │ Probabilistic   │ │ Lookup-Based    │
    │ Estimators         │ │ Estimators      │ │ Estimators      │
    │                    │ │                 │ │                 │
    │ - Brute force      │ │ - PCFG          │ │ - Breach lookup │
    │ - Dictionary       │ │ - Markov/OMEN   │ │                 │
    │ - Rule-based       │ │ - Neural (opt.) │ │                 │
    │ - Keyboard walk    │ │                 │ │                 │
    │ - Mask             │ │                 │ │                 │
    │ - Date/sequence    │ │                 │ │                 │
    │ - Combinator       │ │                 │ │                 │
    │ - Hybrid           │ │                 │ │                 │
    └─────────┬─────────┘ └───────┬────────┘ └────────┬────────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Min-Auto Ensemble   │
                        │  crack_time = min(    │
                        │    all_strategy_times) │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │  Hardware Calculator  │
                        │  guess_number /       │
                        │  hash_rate = seconds  │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Result Formatter    │
                        │  - crack time         │
                        │  - winning attack     │
                        │  - per-strategy detail │
                        │  - strength rating    │
                        │  - explanation        │
                        └──────────────────────┘
```

### Excluded: Rainbow Table Check

Rainbow table attacks are not modeled. Rainbow tables are pre-computed lookup tables that trade storage for computation time, but they are only effective against **unsalted** hashes (e.g., plain MD5, NTLM). All modern password hashing algorithms (bcrypt, scrypt, Argon2id) use per-password salts, rendering rainbow tables ineffective. Since GPU-based cracking dominates for both salted and unsalted hashes, the brute-force and dictionary estimators already cover the relevant attack surface. Rainbow table attacks against unsalted hashes are implicitly bounded by the dictionary/breach lookup estimators.

## Key Design Decisions

1. **Common estimator interface:** Every attack strategy implements `estimate(analysis: PasswordAnalysis) -> EstimateResult`. The password string is available via `analysis.password`. Segment-level estimators return matches for the DP; whole-password estimators return a guess number directly. See [Implementation Roadmap](07-implementation-roadmap.md) for full type definitions.

2. **Shared password analysis:** Tokenization, dictionary lookups, keyboard walk detection, l33t detection, and structural parsing run once. All estimators receive the pre-analyzed result.

3. **Independent estimators:** Each estimator is a self-contained module. Adding a new attack type means adding one file, not touching the core.

4. **Hardware calculation is separate:** Estimators produce guess numbers (strategy-dependent, hardware-independent). The hardware calculator converts guess numbers to seconds (hash-rate-dependent).

## Estimator Registration Mechanism

To satisfy NFR-015 ("Adding a new estimator requires adding one file, no core modifications"), estimators are discovered automatically via module introspection. No explicit registration list is needed.

**Discovery mechanism:** The orchestrator scans the `crack_time.estimators` package at startup, discovers all concrete subclasses of `Estimator`, and instantiates them.

```python
import importlib
import pkgutil
from crack_time.estimators.base import Estimator

def discover_estimators() -> list[Estimator]:
    """Auto-discover all Estimator subclasses in the estimators package.

    To add a new estimator:
      1. Create a new file in crack_time/estimators/ (e.g., my_estimator.py)
      2. Define a class that extends Estimator and implements estimate()
      3. Done — the orchestrator will find and use it automatically.

    Estimators can opt out by setting a class attribute:
      enabled = False
    """
    package = importlib.import_module('crack_time.estimators')
    estimators = []

    for importer, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f'crack_time.estimators.{module_name}')
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                and issubclass(attr, Estimator)
                and attr is not Estimator
                and getattr(attr, 'enabled', True)):
                estimators.append(attr())

    return estimators
```

**Estimator metadata:** Each estimator subclass should declare:

```python
class HybridEstimator(Estimator):
    name = "hybrid"                   # Machine-readable identifier
    display_name = "Hybrid Attack"    # Human-readable name for output
    phase = 2                         # Implementation phase (for phased rollout)
    estimator_type = "whole_password" # "segment_level" or "whole_password"
    enabled = True                    # Set to False to disable without removing

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        ...
```

## Configuration

The simulator is configured via a JSON file (`crack-time.json`) with sensible defaults built in. CLI flags override file-based configuration.

**Configurable categories:**

- **Hardware:** Default hash algorithm, hardware tier, custom hash rates
- **Estimators:** Enable/disable individual estimators, per-estimator timeout
- **Data paths:** Wordlist directory, keyboard graphs, rule files, breach filter, PCFG grammar, Markov tables
- **Rating thresholds:** Time-based strength rating boundaries

The full configuration schema will be finalized during implementation.

## Technology Choices

| Choice | Decision | Rationale |
|--------|----------|-----------|
| Language | Python 3.10+ | All reference tools are Python; direct algorithm reuse |
| Dependencies | Minimal (stdlib + numpy for stats) | Keeps install simple; no heavy ML deps in core |
| Packaging | pip-installable (`pyproject.toml`) | Standard Python distribution |
| CLI | `argparse` or `click` | Simple, no framework overhead |
| Data format | JSON for configs, TSV for lookup tables | Human-readable, easy to inspect |
| Model storage | Text files (PCFG grammar), binary (Markov tables) | Match upstream tool formats for compatibility |
| Testing | `pytest` | Standard Python testing |

## Package Structure

```
password-crack-time-simulator/
├── pyproject.toml
├── README.md
├── src/
│   └── crack_time/
│       ├── __init__.py
│       ├── cli.py                    # Command-line interface
│       ├── simulator.py              # Top-level orchestrator (min-auto ensemble)
│       │
│       ├── analysis/                 # Shared password analysis (run once per password)
│       │   ├── __init__.py
│       │   ├── analyzer.py           # Main analyzer: calls all detectors
│       │   ├── tokenizer.py          # L/D/S/K/Y tokenization (from PCFG)
│       │   ├── keyboard.py           # Adjacency graphs + walk detection
│       │   ├── leet.py               # L33t detection + de-substitution
│       │   ├── dates.py              # Date pattern detection
│       │   ├── sequences.py          # Constant-delta sequence detection
│       │   ├── repeats.py            # Repeat pattern detection
│       │   └── dictionary_lookup.py  # Substring matching against wordlists
│       │
│       ├── estimators/               # One module per attack strategy
│       │   ├── __init__.py
│       │   ├── base.py               # Estimator ABC
│       │   ├── brute_force.py        # charset^length
│       │   ├── dictionary.py         # Rank-based estimation
│       │   ├── rule_based.py         # Rule inversion (UChicago approach)
│       │   ├── keyboard_walk.py      # Spatial formula (zxcvbn)
│       │   ├── mask.py               # Pattern-constrained brute force
│       │   ├── date.py               # Date search space
│       │   ├── sequence.py           # Sequence search space
│       │   ├── repeat.py             # Recursive base evaluation
│       │   ├── combinator.py         # Two-word concatenation
│       │   ├── hybrid.py             # Dictionary + mask suffix/prefix
│       │   ├── pcfg.py               # Grammar probability -> lookup table
│       │   ├── markov.py             # OMEN level-based estimation
│       │   ├── prince.py             # Multi-word probability ordering
│       │   ├── breach.py             # Set membership (Bloom filter)
│       │   └── neural.py             # Monte Carlo CDF estimation (optional)
│       │
│       ├── decomposition/            # DP minimum-cost decomposition
│       │   ├── __init__.py
│       │   └── dp_engine.py          # zxcvbn-style shortest-path DP
│       │
│       ├── hardware/                 # Hash rate and timing calculations
│       │   ├── __init__.py
│       │   ├── hash_rates.py         # Per-algorithm benchmark data
│       │   └── tiers.py              # Hardware tier multipliers
│       │
│       ├── rules/                    # Hashcat/JtR rule parsing and inversion
│       │   ├── __init__.py
│       │   ├── parser.py             # Rule syntax parsing
│       │   ├── operations.py         # Individual ops with apply() + invert()
│       │   └── inverter.py           # Composed rule inversion
│       │
│       └── output/                   # Result formatting
│           ├── __init__.py
│           ├── formatter.py          # Human-readable + JSON output
│           └── rating.py             # 0-4 strength classification
│
├── data/                             # Bundled data assets
│   ├── wordlists/                    # Frequency-ranked wordlists
│   ├── keyboards/                    # Adjacency graph JSON files
│   ├── rules/                        # Hashcat rule files
│   ├── hash_rates.json               # Benchmark data
│   └── masks/                        # Common mask patterns
│
├── tests/
│   ├── test_analyzer.py
│   ├── test_estimators/
│   │   ├── test_brute_force.py
│   │   ├── test_dictionary.py
│   │   ├── test_rule_based.py
│   │   └── ...
│   ├── test_dp_engine.py
│   ├── test_hardware.py
│   └── test_integration.py           # End-to-end tests with known passwords
│
└── scripts/
    ├── build_pcfg_grammar.py          # Train PCFG from password list
    ├── build_markov_tables.py         # Train OMEN tables from password list
    ├── build_pcfg_lookup.py           # Precompute probability -> rank table
    └── download_data.py               # Fetch optional large datasets
```

## Shared Password Analyzer

The shared analyzer runs once per password and produces a `PasswordAnalysis` object consumed by all estimators. This avoids redundant computation — multiple estimators need dictionary lookups, keyboard walk detection, and character class analysis.

### Analysis Pipeline

```
Input: raw password string
  |
  v
[1] Character class detection
    - Identify: digits, lowercase, uppercase, special, unicode
    - Compute cardinality (union of charset sizes)
    - Detect specific character classes at each position
  |
  v
[2] Dictionary substring matching (O(n^2 * D) where D = number of dictionaries)
    - For each (start, end) pair: check lowercase form against each dictionary
    - Record: {token, i, j, dictionary_name, rank, matched_word}
    - Dictionaries: common_passwords (30K), english_words (30K),
                    names (5K), surnames (10K), user_inputs (variable)
  |
  v
[3] L33t-speak detection
    - Scan for substitution characters (@, 3, 0, 1, $, 7, !, etc.)
    - For passwords with l33t chars: enumerate de-l33t variants
    - Run dictionary matching on each variant
    - Record: {token, i, j, sub_table, original_word, rank}
    - Cap enumeration at 2^10 = 1024 variants to prevent pathological cases
  |
  v
[4] Keyboard walk detection
    - Load adjacency graphs (QWERTY, Dvorak, keypad)
    - For each starting position: walk forward checking adjacency
    - Track: direction changes (turns), shifted characters
    - Record walks of length >= 3: {token, i, j, graph, turns, shifted_count}
  |
  v
[5] Sequence detection
    - For each position: check if delta between consecutive chars is constant
    - Accept deltas of +1, -1, +2, -2 with minimum length 3
    - Record: {token, i, j, sequence_type, ascending, delta}
  |
  v
[6] Date detection
    - Extract candidate substrings (length 4-10)
    - Try all date format parsings (MMDDYYYY, DDMMYY, YYYYMMDD, etc.)
    - With and without separators (/, -, .)
    - Validate month (1-12), day (1-31), year (plausible range)
    - Record: {token, i, j, year, month, day, separator}
  |
  v
[7] Repeat detection
    - Greedy regex: (.+)\1+ to find longest repeated sequence
    - Lazy regex: (.+?)\1+ to find shortest repeating unit
    - Take whichever yields fewer guesses
    - Recursively analyze base token (call full analyzer)
    - Record: {token, i, j, base_token, base_analysis, repeat_count}
  |
  v
[8] PCFG structure tokenization
    - Decompose into L/D/S/K/Y tokens using PCFG detection priority:
      keyboard walks > years/dates > leet-speak > basic L/D/S
    - Record structure string (e.g., "L6D2S1")
  |
  v
Output: PasswordAnalysis (all detected patterns, ready for estimators)
```

## Hardware Reference Data

### Single-GPU Hash Rates (RTX 4090 baseline)

| Algorithm | Hash Rate | Relative to MD5 |
|-----------|-----------|-----------------|
| NTLM | 288.5 GH/s | 1.76x |
| MD5 | 164.1 GH/s | 1.0x (baseline) |
| SHA-1 | 50.6 GH/s | 0.31x |
| SHA-256 | 22.0 GH/s | 0.13x |
| SHA-512 | 7.5 GH/s | 0.046x |
| PBKDF2-SHA256 | 8.9 MH/s | 0.000054x |
| bcrypt (cost=5) | 184 kH/s | 0.0000011x |
| bcrypt (cost=12) | 1,437 H/s | 0.0000000088x |
| scrypt | 7,126 H/s | 0.000000043x |
| Argon2id (64 MiB) | ~600 H/s | 0.0000000037x |

### Hardware Tier Multipliers (vs. single RTX 4090)

| Tier | Description | Multiplier |
|------|-------------|-----------|
| Budget | GTX 1080 Ti | 0.19x |
| Consumer | RTX 4090 | 1.0x |
| Enthusiast | RTX 5090 | 1.34x |
| Small Rig | 4x RTX 4090 | 3.6x |
| Large Rig | 8x RTX 4090 | 7.0x |
| Dedicated | 14x RTX 4090 | 12.2x |
| Well-Funded | ~100 GPUs | 85x |
| Nation-State | 10K--100K GPUs | 8,500--85,000x |

### Ready-to-Use Hash Rate Dictionary

```python
HASH_RATES_PER_GPU = {
    "md5":              164_100_000_000,    # 164.1 GH/s
    "sha1":              50_638_700_000,    # 50.6 GH/s
    "sha256":            21_975_500_000,    # 22.0 GH/s
    "sha512":             7_483_400_000,    # 7.5 GH/s
    "ntlm":             288_500_000_000,    # 288.5 GH/s
    "bcrypt_cost5":             184_000,
    "bcrypt_cost10":              5_750,    # 184000 / 2^5
    "bcrypt_cost12":              1_437,    # 184000 / 2^7
    "scrypt_default":             7_126,
    "argon2id_64m_t3":              600,
    "pbkdf2_sha256":      8_865_700,
    "wpa_wpa2":           2_533_300,
}
```

### Hardware Calculator

**Tier multipliers are pre-baked.** The multipliers in the table above already incorporate multi-GPU scaling losses (efficiency drops ~10-15% per GPU for fast hashes, ~5% for slow hashes). This means the hardware calculator is a simple lookup — no per-algorithm scaling factor needed at query time.

```python
HARDWARE_TIERS = {
    "budget":       {"description": "GTX 1080 Ti",       "multiplier": 0.19},
    "consumer":     {"description": "RTX 4090",          "multiplier": 1.0},
    "enthusiast":   {"description": "RTX 5090",          "multiplier": 1.34},
    "small_rig":    {"description": "4x RTX 4090",       "multiplier": 3.6},
    "large_rig":    {"description": "8x RTX 4090",       "multiplier": 7.0},
    "dedicated":    {"description": "14x RTX 4090",      "multiplier": 12.2},
    "well_funded":  {"description": "~100 GPUs",         "multiplier": 85.0},
    "nation_state": {"description": "10K+ GPUs",         "multiplier": 8500.0},
}

def crack_time_seconds(guess_number: int, algorithm: str, hardware_tier: str) -> float:
    base_rate = HASH_RATES_PER_GPU[algorithm]
    multiplier = HARDWARE_TIERS[hardware_tier]["multiplier"]
    effective_rate = base_rate * multiplier
    if effective_rate == 0:
        return float('inf')
    return guess_number / effective_rate
```

**bcrypt cost factor derivation:** For bcrypt costs not in the lookup table, derive from the cost=5 baseline:

```python
def bcrypt_hash_rate(cost: int) -> float:
    """Derive hash rate for any bcrypt cost from the cost=5 benchmark.
    Each +1 cost doubles the work, halving the hash rate."""
    return HASH_RATES_PER_GPU["bcrypt_cost5"] / (2 ** (cost - 5))

# Examples:
#   bcrypt_cost5  = 184,000 H/s   (benchmark)
#   bcrypt_cost10 = 184,000 / 32  = 5,750 H/s
#   bcrypt_cost12 = 184,000 / 128 = 1,437 H/s
#   bcrypt_cost14 = 184,000 / 512 = 359 H/s
```

**Multi-GPU scaling background (for reference, not used at runtime):** The pre-baked tier multipliers were derived from benchmarks using this model:

```
effective_speed = single_gpu_speed * num_gpus * scaling_efficiency

scaling_efficiency by algorithm type:
  Fast hashes (MD5, NTLM):       ~0.87 per GPU (bandwidth-limited)
  Medium hashes (SHA-*, PBKDF2): ~0.92 per GPU
  Slow hashes (bcrypt, scrypt):  ~0.97 per GPU (compute-limited, scales near-linearly)
```

The tier multipliers use the midpoint efficiency. For example, 8x RTX 4090 with ~0.87 efficiency = 8 * 0.87 = 6.96, rounded to 7.0x. If more precision is needed for a specific algorithm, a future version could store per-algorithm-class multipliers per tier.

## Architectural Patterns by Source

| Pattern | zxcvbn | UChicago | CMU | OMEN/Framework | PCFG |
|---------|--------|----------|-----|----------------|------|
| Min-across-strategies | Yes (DP) | No (single) | Yes (min-auto) | Yes (compare) | No (single) |
| Strategy plugin interface | No (hardcoded) | No | Yes | Yes | No |
| Analytical guess estimation | Yes | Yes | Yes (for some) | Partial (levels) | Via lookup table |
| Monte Carlo estimation | No | No | Yes | No | Possible |
| Precomputed lookup tables | No | No | Yes | Yes (level counts) | Recommended |
| Keyboard adjacency graphs | Yes | No | No | No | Yes |
| L33t substitution handling | Yes | No | No | No | Yes |
| Frequency-ranked dictionaries | Yes | Yes | Yes | Yes | Yes |
| Configuration-driven | No | Partial | Yes | Yes | Partial |

---

See also: [Project Overview](01-project-overview.md) | [Estimator Specs](05-estimator-specs.md) | [Data & Models](06-data-and-models.md)

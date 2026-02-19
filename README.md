# Password Crack-Time Simulator

A tool that estimates how long a password would take to crack by modeling **all realistic attack strategies simultaneously** and returning the minimum time across all of them.

## The Problem

Every existing password strength tool evaluates from a single attack perspective. No production tool models dictionary attacks, rule-based mangling, Markov chains, PCFG, keyboard walks, breach lookups, and brute force simultaneously. This simulator does.

## The Core Formula

```
crack_time = min(
    time_breach_lookup,   time_dictionary,     time_rule_based,
    time_combinator,      time_hybrid,         time_mask,
    time_keyboard_walk,   time_prince,         time_pcfg,
    time_markov,          time_neural,         time_brute_force
)
```

Each `time_X = guess_number_X / hash_rate`, where hash rate depends on the hash algorithm and attacker hardware.

## Example Output

```
$ crack-time estimate "Summer2024!" --hash bcrypt_cost12 --hardware rig_8x_rtx4090

Crack Time:   ~1.4 hours
Rating:       WEAK (1/4)
Winner:       Hybrid attack (dictionary + mask ?d?d?d?d?s)
```

## Status

**Research complete, implementation planned.** Eight research reports are done. The architecture, estimator specifications, and four-phase implementation roadmap are documented.

## Documentation

All project documentation lives in [`docs/`](docs/index.md):

- [Project Overview](docs/01-project-overview.md) — What and why
- [Requirements](docs/02-requirements.md) — Formal FR/NFR specs
- [Use Cases](docs/03-use-cases.md) — 7 usage scenarios
- [Architecture](docs/04-architecture.md) — System design and package structure
- [Estimator Specs](docs/05-estimator-specs.md) — 15 attack estimators + DP engine
- [Data & Models](docs/06-data-and-models.md) — External data requirements
- [Implementation Roadmap](docs/07-implementation-roadmap.md) — 4-phase build plan
- [Validation Strategy](docs/08-validation-strategy.md) — Test methodology and output format
- [Open Questions](docs/09-open-questions.md) — Unresolved design decisions
- [References](docs/10-references.md) — Papers, tools, benchmarks
- [Research Reports](docs/research/) — 8 in-depth research studies

## Key Research Findings

- **Hash algorithm dominates:** MD5 to bcrypt cost=12 is ~114 million times slower. Hash choice matters more than attacker hardware.
- **Min-auto validated:** The minimum-across-all-strategies approach appears independently in CMU, zxcvbn, and the academic literature.
- **15 attack techniques:** Real cracking uses a four-phase pipeline from instant lookups to exhaustive brute force.
- **All reference tools are Python:** Confirms Python 3.10+ as the implementation language.

## Repository Structure

```
password-cracking/
├── README.md                          ← You are here
├── PROJECT.md                         ← Original project definition
├── docs/                              ← All documentation
│   ├── index.md                       ← Documentation hub
│   ├── 01-project-overview.md
│   ├── ...
│   └── research/                      ← 8 research reports
├── analytic-password-cracking/        ← UChicago tool (external repo)
└── mxr-m301-bass-synth/              ← Unrelated (separate project)
```

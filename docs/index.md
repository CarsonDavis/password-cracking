# Password Crack-Time Simulator — Documentation

Central hub for all project documentation. The simulator estimates how long a password would take to crack by modeling 15 attack strategies simultaneously and returning the minimum time across all of them.

---

## Project Documents

### [01 — Project Overview & Research Synthesis](01-project-overview.md)
What the simulator is, why it exists, the core formula, and key findings from eight research reports.

### [02 — Requirements Specification](02-requirements.md)
Formal functional requirements (FR-001 through FR-037), non-functional requirements (NFR-001 through NFR-017), and testable acceptance criteria.

### [03 — Use Cases](03-use-cases.md)
Seven use cases: single password evaluation, batch audit, passphrase comparison, hash algorithm impact, attacker profiles, library integration, and targeted attack simulation.

### [04 — System Architecture](04-architecture.md)
Pipeline design, technology choices (Python 3.10+, minimal deps), package structure, shared analysis layer, and hardware reference data including the `HASH_RATES_PER_GPU` dictionary.

### [05 — Estimator Specifications & DP Engine](05-estimator-specs.md)
Detailed specs for all 15 attack estimators with pseudocode, the DP decomposition algorithm, accuracy characteristics, and formulas for uppercase/l33t/spatial variation counting.

### [06 — External Data & Model Requirements](06-data-and-models.md)
All required data assets (wordlists, keyboard graphs, rule files, trained models, breach data), their sources, sizes, licensing, and acquisition instructions.

### [07 — Implementation Roadmap](07-implementation-roadmap.md)
Four-phase build plan with 24 deliverables: Phase 1 (core + analytical), Phase 2 (probabilistic + rules), Phase 3 (advanced + polish), Phase 4 (neural + validation).

### [08 — Validation Strategy & Output Format](08-validation-strategy.md)
Unit and system-level validation methodology, 21 test passwords with expected winners, output format examples (CLI and JSON), and the 0-4 strength rating scale.

### [09 — Open Questions & Design Decisions](09-open-questions.md)
Twelve unresolved design decisions (dictionary size, training data, Bloom filter tradeoffs, rule scope, i18n, NIST alignment, etc.) plus the four original motivating questions.

### [10 — References](10-references.md)
Academic papers (13 publications, 2009-2023), tools and data sources (11 resources), and benchmark sources (5 GPU benchmark gists).

## Research Reports

### [Research Directory](research/)
Eight research reports across two phases. Phase 1 surveyed hardware benchmarks, cracking techniques, and existing tools. Phase 2 deep-dived into zxcvbn, UChicago analytic cracking, CMU guess-calculator, OMEN/Password-Guessing-Framework, and PCFG Cracker.

---

## Quick Links

| Topic | Document |
|-------|----------|
| "What does this project do?" | [Project Overview](01-project-overview.md) |
| "What are the requirements?" | [Requirements](02-requirements.md) |
| "How is it designed?" | [Architecture](04-architecture.md) |
| "How do estimators work?" | [Estimator Specs](05-estimator-specs.md) |
| "What data do I need?" | [Data & Models](06-data-and-models.md) |
| "What's the build plan?" | [Implementation Roadmap](07-implementation-roadmap.md) |
| "How do we test it?" | [Validation Strategy](08-validation-strategy.md) |
| "What's still undecided?" | [Open Questions](09-open-questions.md) |

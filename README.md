# Password Crack-Time Simulator

A tool that estimates how long a password would take to crack by modeling **all realistic attack strategies simultaneously** and returning the minimum time across all of them.

## Quick Start

### Prerequisites
- Python 3.10+ with [uv](https://docs.astral.sh/uv/)
- Node.js 18+ (for the web frontend)

### Install & Run

```bash
# Install Python dependencies
uv sync --all-packages

# Run the CLI
uv run crack-time estimate "password" --hash bcrypt_cost12 --hardware consumer

# Start the API server
uv run crack-time-api    # http://localhost:8000

# Start the web frontend (in a second terminal)
cd packages/web && npm install && npm run dev    # http://localhost:5173
```

## The Core Formula

```
crack_time = min(
    time_dictionary,     time_mask,           time_keyboard_walk,
    time_date,           time_sequence,       time_repeat,
    time_l33t,           time_brute_force
)
```

Each `time_X = guess_number_X / hash_rate`, where hash rate depends on the hash algorithm and attacker hardware.

## Example Output

```
$ uv run crack-time estimate "Summer2024!" --hash bcrypt_cost12 --hardware consumer

Password:     'Summer2024!'
Hash:         bcrypt_cost12
Hardware:     consumer (1,437 H/s effective)

Crack Time:   ~...
Rating:       ... (X/4)
Winner:       ...
```

## Repository Structure

```
password-cracking/                      # monorepo root
├── pyproject.toml                      # uv workspace coordinator
├── data/                               # shared data assets
│   ├── hash_rates.json
│   ├── l33t_table.json
│   ├── keyboards/                      # qwerty.json, dvorak.json, keypad.json
│   ├── masks/                          # common_masks.json
│   └── wordlists/                      # common_passwords.txt, english_words.txt, etc.
│
├── docs/                               # specification & research docs
│   ├── index.md
│   ├── 01-project-overview.md ... 10-references.md
│   └── research/                       # 8 research reports
│
├── packages/
│   ├── crack-time/                     # core Python library
│   │   ├── pyproject.toml
│   │   ├── src/crack_time/             # analysis, estimators, decomposition, hardware, output
│   │   └── tests/
│   │
│   ├── api/                            # FastAPI server
│   │   ├── pyproject.toml
│   │   ├── src/crack_time_api/         # app, schemas, routers
│   │   └── tests/
│   │
│   └── web/                            # SvelteKit frontend
│       ├── package.json
│       ├── src/                        # routes, components, stores
│       └── static/
│
└── reference/                          # external tools (gitignored)
```

## Documentation

All project documentation lives in [`docs/`](docs/index.md):

- [Project Overview](docs/01-project-overview.md)
- [Requirements](docs/02-requirements.md)
- [Use Cases](docs/03-use-cases.md)
- [Architecture](docs/04-architecture.md)
- [Estimator Specs](docs/05-estimator-specs.md)
- [Data & Models](docs/06-data-and-models.md)
- [Implementation Roadmap](docs/07-implementation-roadmap.md)
- [Validation Strategy](docs/08-validation-strategy.md)
- [Open Questions](docs/09-open-questions.md)
- [References](docs/10-references.md)
- [Research Reports](docs/research/)

## Development

```bash
# Terminal 1 — API server
uv run crack-time-api

# Terminal 2 — Frontend dev server
cd packages/web && npm run dev

# Terminal 3 — Run all Python tests
uv run pytest
```

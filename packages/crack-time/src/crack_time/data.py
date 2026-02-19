"""Centralized data loading with lazy initialization."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


def _find_data_dir() -> Path:
    """Locate the data directory by env var or walking up from this file."""
    env_dir = os.environ.get("CRACK_TIME_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "data"
        if candidate.is_dir() and any(candidate.iterdir()):
            return candidate
        current = current.parent
    raise FileNotFoundError("Cannot find data directory. Set CRACK_TIME_DATA_DIR.")


DATA_DIR = _find_data_dir()


class Wordlist:
    """A frequency-ranked wordlist with O(1) rank lookup and membership test."""

    def __init__(self, words: list[str]):
        self._words = words
        self._rank_map: dict[str, int] = {}
        for i, word in enumerate(words):
            w = word.lower()
            if w not in self._rank_map:
                self._rank_map[w] = i + 1  # 1-based rank

    def rank(self, word: str) -> int:
        """Return 1-based rank of word, or 0 if not found."""
        return self._rank_map.get(word.lower(), 0)

    def __contains__(self, word: str) -> bool:
        return word.lower() in self._rank_map

    @property
    def size(self) -> int:
        return len(self._words)


@lru_cache(maxsize=None)
def load_wordlist(name: str) -> Wordlist:
    """Load a wordlist from data/wordlists/{name}.txt."""
    path = DATA_DIR / "wordlists" / f"{name}.txt"
    words = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                words.append(word)
    return Wordlist(words)


@lru_cache(maxsize=None)
def load_adjacency_graph(name: str) -> dict:
    """Load a keyboard adjacency graph from data/keyboards/{name}.json."""
    path = DATA_DIR / "keyboards" / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load_l33t_table() -> dict[str, list[str]]:
    """Load the l33t substitution table."""
    path = DATA_DIR / "l33t_table.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load_mask_library() -> list[dict]:
    """Load the common mask pattern library."""
    path = DATA_DIR / "masks" / "common_masks.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load_hash_rates() -> dict[str, int]:
    """Load GPU hash rate benchmarks."""
    path = DATA_DIR / "hash_rates.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_data_files() -> list[str]:
    """Check that all required data files exist. Returns list of missing files."""
    required = [
        DATA_DIR / "wordlists" / "common_passwords.txt",
        DATA_DIR / "wordlists" / "english_words.txt",
        DATA_DIR / "wordlists" / "names.txt",
        DATA_DIR / "wordlists" / "surnames.txt",
        DATA_DIR / "keyboards" / "qwerty.json",
        DATA_DIR / "keyboards" / "dvorak.json",
        DATA_DIR / "keyboards" / "keypad.json",
        DATA_DIR / "l33t_table.json",
        DATA_DIR / "masks" / "common_masks.json",
        DATA_DIR / "hash_rates.json",
    ]
    return [str(p) for p in required if not p.exists()]


def get_all_wordlists() -> dict[str, Wordlist]:
    """Load all standard wordlists and return as a name->Wordlist dict."""
    names = ["common_passwords", "english_words", "names", "surnames"]
    return {name: load_wordlist(name) for name in names}


def graph_stats(graph: dict) -> tuple[int, float]:
    """Compute starting_positions and avg_degree for an adjacency graph."""
    starting_positions = len(graph)
    total_degree = 0
    for neighbors in graph.values():
        total_degree += sum(1 for n in neighbors if n is not None)
    avg_degree = total_degree / starting_positions if starting_positions else 0
    return starting_positions, avg_degree

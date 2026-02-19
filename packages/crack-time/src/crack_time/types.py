"""Core type definitions for the password crack-time simulator."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Match:
    """A detected pattern covering password[i..j] (inclusive).
    Produced by the analyzer; consumed by estimators and the DP engine."""
    pattern: str           # 'dictionary', 'spatial', 'sequence', 'date',
                           # 'repeat', 'l33t', 'brute_force'
    token: str             # The substring password[i..j+1]
    i: int                 # Start index (inclusive)
    j: int                 # End index (inclusive)
    guesses: int = 0       # Estimated guesses for this match (set by estimator)


@dataclass
class DictionaryMatch(Match):
    """Substring found in a frequency-ranked wordlist."""
    word: str = ""
    rank: int = 0
    dictionary_name: str = ""
    reversed: bool = False


@dataclass
class L33tMatch(Match):
    """Dictionary match found after de-l33t substitution."""
    word: str = ""
    rank: int = 0
    dictionary_name: str = ""
    sub_table: dict = field(default_factory=dict)


@dataclass
class KeyboardWalkMatch(Match):
    """Spatial pattern on a keyboard adjacency graph."""
    graph: str = ""
    turns: int = 0
    shifted_count: int = 0


@dataclass
class SequenceMatch(Match):
    """Constant-delta character sequence (abc, 135, zyx)."""
    sequence_name: str = ""
    ascending: bool = True
    delta: int = 0


@dataclass
class DateMatch(Match):
    """Calendar date pattern."""
    year: int = 0
    month: int = 0
    day: int = 0
    separator: str = ""
    has_separator: bool = False


@dataclass
class RepeatMatch(Match):
    """Repeated character or subsequence."""
    base_token: str = ""
    base_guesses: int = 0
    repeat_count: int = 0


@dataclass
class BruteforceMatch(Match):
    """Fallback match for unmatched segments in the DP decomposition."""
    cardinality: int = 0


@dataclass
class PasswordAnalysis:
    """Shared analysis result, computed once per password."""
    password: str
    length: int
    charsets: set[str] = field(default_factory=set)
    cardinality: int = 0
    matches: list[Match] = field(default_factory=list)

    def matches_of_type(self, pattern: str) -> list[Match]:
        return [m for m in self.matches if m.pattern == pattern]


@dataclass
class EstimateResult:
    """Result from a single estimator."""
    guess_number: int | float  # float('inf') if not applicable
    attack_name: str
    details: dict = field(default_factory=dict)
    matches: list[Match] = field(default_factory=list)


@dataclass
class DecompositionResult:
    """Result from the DP decomposition engine."""
    guesses: int
    sequence: list[Match] = field(default_factory=list)
    log10_guesses: float = 0.0


@dataclass
class SimulationResult:
    """Top-level result from the full simulation pipeline."""
    password: str
    hash_algorithm: str
    hardware_tier: str
    effective_hash_rate: float
    guess_number: int | float
    crack_time_seconds: float
    crack_time_display: str
    rating: int
    rating_label: str
    winning_attack: str
    strategies: dict = field(default_factory=dict)
    decomposition: list[dict] = field(default_factory=list)

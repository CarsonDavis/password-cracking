"""Main password analyzer: calls all detectors in order."""

from __future__ import annotations

from crack_time.analysis.character_classes import compute_cardinality, detect_charsets
from crack_time.analysis.dates import detect_dates
from crack_time.analysis.dictionary_lookup import detect_dictionary_matches
from crack_time.analysis.keyboard import detect_keyboard_walks
from crack_time.analysis.leet import detect_l33t_matches
from crack_time.analysis.repeats import detect_repeats
from crack_time.analysis.sequences import detect_sequences
from crack_time.data import get_all_wordlists, load_adjacency_graph, load_l33t_table
from crack_time.types import PasswordAnalysis


def analyze(password: str) -> PasswordAnalysis:
    """Run the full analysis pipeline on a password.

    Steps:
    [1] Character class detection + cardinality
    [2] Dictionary substring matching
    [3] L33t detection
    [4] Keyboard walk detection
    [5] Sequence detection
    [6] Date detection
    [7] Repeat detection
    """
    # Strip null bytes
    password = password.replace("\x00", "")

    # [1] Character classes
    charsets = detect_charsets(password)
    cardinality = compute_cardinality(charsets)

    analysis = PasswordAnalysis(
        password=password,
        length=len(password),
        charsets=charsets,
        cardinality=cardinality,
    )

    if not password:
        return analysis

    # [2] Dictionary matching
    wordlists = get_all_wordlists()
    dict_matches = detect_dictionary_matches(password, wordlists)
    analysis.matches.extend(dict_matches)

    # [3] L33t detection
    l33t_table = load_l33t_table()
    l33t_matches = detect_l33t_matches(password, l33t_table, wordlists)
    analysis.matches.extend(l33t_matches)

    # [4] Keyboard walk detection
    graphs = {
        name: load_adjacency_graph(name)
        for name in ("qwerty", "dvorak", "keypad")
    }
    keyboard_matches = detect_keyboard_walks(password, graphs)
    analysis.matches.extend(keyboard_matches)

    # [5] Sequence detection
    seq_matches = detect_sequences(password)
    analysis.matches.extend(seq_matches)

    # [6] Date detection
    date_matches = detect_dates(password)
    analysis.matches.extend(date_matches)

    # [7] Repeat detection
    repeat_matches = detect_repeats(password)
    analysis.matches.extend(repeat_matches)

    return analysis

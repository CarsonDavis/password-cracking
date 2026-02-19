"""Keyboard walk detection using adjacency graphs."""

from __future__ import annotations

from crack_time.types import KeyboardWalkMatch

MIN_WALK_LENGTH = 3


def detect_keyboard_walks(
    password: str, graphs: dict[str, dict]
) -> list[KeyboardWalkMatch]:
    """Detect keyboard walk patterns across all provided adjacency graphs."""
    matches: list[KeyboardWalkMatch] = []
    for graph_name, graph in graphs.items():
        matches.extend(_detect_walks_for_graph(password, graph_name, graph))
    return matches


def _detect_walks_for_graph(
    password: str, graph_name: str, graph: dict
) -> list[KeyboardWalkMatch]:
    """Detect walks on a single keyboard graph."""
    matches: list[KeyboardWalkMatch] = []
    n = len(password)
    if n < MIN_WALK_LENGTH:
        return matches

    i = 0
    while i < n - 1:
        j = i + 1
        last_direction = -1
        turns = 0
        shifted_count = int(_is_shifted(password[i]))

        if password[i].lower() not in graph:
            i += 1
            continue

        while j < n:
            cur_char = password[j].lower()
            prev_char = password[j - 1].lower()

            if prev_char not in graph:
                break

            neighbors = graph[prev_char]
            direction = _find_direction(neighbors, cur_char)

            if direction == -1:
                break

            if last_direction == -1:
                # First step: counts as the first turn (per zxcvbn convention)
                turns = 1
            elif direction != last_direction:
                turns += 1
            last_direction = direction

            if _is_shifted(password[j]):
                shifted_count += 1

            j += 1

        walk_length = j - i
        if walk_length >= MIN_WALK_LENGTH:
            matches.append(
                KeyboardWalkMatch(
                    pattern="spatial",
                    token=password[i:j],
                    i=i,
                    j=j - 1,
                    graph=graph_name,
                    turns=turns,
                    shifted_count=shifted_count,
                )
            )
            i = j
        else:
            i += 1

    return matches


def _find_direction(neighbors: list, target_char: str) -> int:
    """Find which direction index (0-5) leads to the target character."""
    for direction, neighbor in enumerate(neighbors):
        if neighbor is not None and neighbor.lower() == target_char:
            return direction
    return -1


def _is_shifted(char: str) -> bool:
    """Check if a character requires the shift key."""
    return char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'

"""Output formatting: human-readable and JSON."""

from __future__ import annotations

import json

from crack_time.types import SimulationResult


def format_time(seconds: float) -> str:
    """Convert seconds to human-readable time string."""
    if seconds == 0:
        return "instant"
    if seconds == float("inf"):
        return "infinite"
    if seconds < 1:
        return "< 1 second"
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    if seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    if seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    if seconds < 31557600:
        days = seconds / 86400
        if days < 30:
            return f"{days:.0f} days"
        months = days / 30.44
        return f"{months:.1f} months"
    years = seconds / 31557600
    if years < 100:
        return f"{years:.1f} years"
    if years < 1000:
        return f"{years:.0f} years"
    if years < 1_000_000:
        return f"{years/1000:.0f} thousand years"
    if years < 1_000_000_000:
        return f"{years/1_000_000:.0f} million years"
    return f"{years/1_000_000_000:.0f} billion years"


def format_human(result: SimulationResult) -> str:
    """Format result as human-readable text."""
    lines = [
        f"Password:     {result.password!r}",
        f"Hash:         {result.hash_algorithm}",
        f"Hardware:     {result.hardware_tier} ({result.effective_hash_rate:,.0f} H/s effective)",
        "",
        f"Crack Time:   ~{result.crack_time_display}",
        f"Rating:       {result.rating_label} ({result.rating}/4)",
        f"Winner:       {result.winning_attack}",
    ]

    if result.strategies:
        lines.append("")
        lines.append("Strategy Breakdown:")
        for name, info in result.strategies.items():
            guess_num = info.get("guess_number")
            if guess_num is None or guess_num == float("inf") or guess_num == "infinity":
                lines.append(f"  {name:20s} NOT APPLICABLE")
            else:
                lines.append(f"  {name:20s} {guess_num:,.0f} guesses")

    if result.decomposition:
        lines.append("")
        parts = []
        for seg in result.decomposition:
            parts.append(f'["{seg["segment"]}" ({seg["type"]})]')
        lines.append(f"Decomposition: {' + '.join(parts)}")

    return "\n".join(lines)


def _sanitize_strategies(strategies: dict) -> dict:
    """Convert float('inf') to 'infinity' in strategy dicts for JSON safety."""
    sanitized = {}
    for name, info in strategies.items():
        sanitized[name] = {
            k: ("infinity" if v == float("inf") else v)
            for k, v in info.items()
        }
    return sanitized


def format_json(result: SimulationResult) -> str:
    """Format result as JSON string."""
    data = {
        "password": result.password,
        "hash_algorithm": result.hash_algorithm,
        "hardware_tier": result.hardware_tier,
        "effective_hash_rate": result.effective_hash_rate,
        "guess_number": result.guess_number if result.guess_number != float("inf") else "infinity",
        "crack_time_seconds": result.crack_time_seconds if result.crack_time_seconds != float("inf") else "infinity",
        "crack_time_display": result.crack_time_display,
        "rating": result.rating,
        "rating_label": result.rating_label,
        "winning_attack": result.winning_attack,
        "strategies": _sanitize_strategies(result.strategies),
        "decomposition": result.decomposition,
    }
    return json.dumps(data, indent=2)

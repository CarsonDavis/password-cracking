"""Click-based CLI for the password crack-time simulator."""

from __future__ import annotations

import json
import sys

import click

from crack_time.data import validate_data_files
from crack_time.output.formatter import format_human, format_json
from crack_time.simulator import estimate_password


@click.group()
def main():
    """Password crack-time simulator."""
    missing = validate_data_files()
    if missing:
        click.echo(f"Warning: missing data files: {', '.join(missing)}", err=True)


@main.command()
@click.argument("password")
@click.option("--hash", "algorithm", default="bcrypt_cost12",
              help="Hash algorithm (e.g. bcrypt_cost12, md5, sha256)")
@click.option("--hardware", "hardware_tier", default="consumer",
              help="Hardware tier (e.g. consumer, large_rig, nation_state)")
@click.option("--json", "use_json", is_flag=True,
              help="Output as JSON")
def estimate(password: str, algorithm: str, hardware_tier: str, use_json: bool):
    """Estimate crack time for a single password."""
    try:
        result = estimate_password(password, algorithm, hardware_tier)
    except (ValueError, TypeError) as e:
        if use_json:
            click.echo(json.dumps({"error": True, "message": str(e)}))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if use_json:
        click.echo(format_json(result))
    else:
        click.echo(format_human(result))


@main.command()
@click.argument("password_file", type=click.Path(exists=True))
@click.option("--hash", "algorithm", default="bcrypt_cost12",
              help="Hash algorithm")
@click.option("--hardware", "hardware_tier", default="consumer",
              help="Hardware tier")
@click.option("--json", "use_json", is_flag=True,
              help="Output as JSON")
def batch(password_file: str, algorithm: str, hardware_tier: str, use_json: bool):
    """Evaluate a batch of passwords from a file."""
    with open(password_file, encoding="utf-8") as f:
        passwords = [line.strip() for line in f if line.strip()]

    results = []
    for pw in passwords:
        try:
            result = estimate_password(pw, algorithm, hardware_tier)
            results.append(result)
        except Exception as e:
            click.echo(f"Error processing '{pw}': {e}", err=True)

    if use_json:
        _output_batch_json(results, passwords, algorithm, hardware_tier)
    else:
        _output_batch_human(results)


def _output_batch_json(results, passwords, algorithm, hardware_tier):
    """Output batch results as JSON."""
    rating_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    attack_dist: dict[str, int] = {}

    for r in results:
        rating_dist[r.rating] = rating_dist.get(r.rating, 0) + 1
        attack_dist[r.winning_attack] = attack_dist.get(r.winning_attack, 0) + 1

    crack_times = sorted(r.crack_time_seconds for r in results)
    median_ct = crack_times[len(crack_times) // 2] if crack_times else 0

    data = {
        "total_passwords": len(results),
        "summary": {
            "median_crack_time_seconds": median_ct,
            "rating_distribution": rating_dist,
            "winning_attack_distribution": attack_dist,
        },
        "passwords": [
            {
                "password": r.password,
                "crack_time_seconds": r.crack_time_seconds,
                "crack_time_display": r.crack_time_display,
                "rating": r.rating,
                "rating_label": r.rating_label,
                "winning_attack": r.winning_attack,
                "guess_number": r.guess_number if r.guess_number != float("inf") else "infinity",
            }
            for r in results
        ],
    }
    click.echo(json.dumps(data, indent=2))


def _output_batch_human(results):
    """Output batch results in human-readable format."""
    click.echo(f"Evaluated: {len(results)} passwords")

    if not results:
        return

    crack_times = sorted(r.crack_time_seconds for r in results)
    from crack_time.output.formatter import format_time
    median_ct = crack_times[len(crack_times) // 2]
    click.echo(f"Median crack time: {format_time(median_ct)}")

    rating_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    from crack_time.output.rating import RATING_LABELS
    for r in results:
        rating_dist[r.rating] += 1

    click.echo("\nRating Distribution:")
    for rating in range(5):
        count = rating_dist[rating]
        pct = count / len(results) * 100
        bar = "#" * int(pct / 2)
        label = RATING_LABELS[rating]
        click.echo(f"  {label:14s} ({rating}): {count:5d} ({pct:5.1f}%)  {bar}")

    # Weakest passwords
    weakest = sorted(results, key=lambda r: r.crack_time_seconds)[:5]
    click.echo("\nWeakest Passwords:")
    for i, r in enumerate(weakest, 1):
        click.echo(f"  {i}. {r.password!r:20s} -> {r.crack_time_display:15s} ({r.winning_attack})")

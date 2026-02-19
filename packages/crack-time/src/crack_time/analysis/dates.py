"""Date pattern detection in passwords."""

from __future__ import annotations

import datetime

from crack_time.types import DateMatch

SEPARATORS = ["/", "-", "."]


def detect_dates(password: str) -> list[DateMatch]:
    """Detect calendar date patterns in the password."""
    matches: list[DateMatch] = []
    n = len(password)

    # Try substrings of length 4-10
    for i in range(n):
        for length in range(4, min(11, n - i + 1)):
            j = i + length - 1
            token = password[i : j + 1]
            date_matches = _try_parse_date(token, i, j)
            matches.extend(date_matches)

    return _deduplicate(matches)


def _try_parse_date(token: str, i: int, j: int) -> list[DateMatch]:
    """Try to parse a token as a date in various formats."""
    results: list[DateMatch] = []

    # Try without separator
    digits = token
    if digits.isdigit():
        results.extend(_parse_no_separator(digits, i, j))

    # Try with separator
    for sep in SEPARATORS:
        if sep in token:
            parts = token.split(sep)
            if len(parts) == 3:
                results.extend(_parse_with_separator(parts, sep, i, j, token))
            elif len(parts) == 2:
                results.extend(_parse_with_separator_2part(parts, sep, i, j, token))

    return results


def _parse_no_separator(digits: str, i: int, j: int) -> list[DateMatch]:
    """Parse digits-only date patterns."""
    results: list[DateMatch] = []
    n = len(digits)

    if n == 8:
        # MMDDYYYY
        m, d, y = int(digits[0:2]), int(digits[2:4]), int(digits[4:8])
        if _valid_date(y, m, d):
            results.append(_make_match(digits, i, j, y, m, d, "", False))

        # DDMMYYYY
        d2, m2, y2 = int(digits[0:2]), int(digits[2:4]), int(digits[4:8])
        if m2 != m and _valid_date(y2, m2, d2):
            results.append(_make_match(digits, i, j, y2, m2, d2, "", False))

        # YYYYMMDD
        y3, m3, d3 = int(digits[0:4]), int(digits[4:6]), int(digits[6:8])
        if _valid_date(y3, m3, d3):
            results.append(_make_match(digits, i, j, y3, m3, d3, "", False))

    elif n == 6:
        # MMDDYY
        m, d, y = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
        y = _expand_year(y)
        if _valid_date(y, m, d):
            results.append(_make_match(digits, i, j, y, m, d, "", False))

        # DDMMYY
        d2, m2, y2 = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
        y2 = _expand_year(y2)
        if m2 != m and _valid_date(y2, m2, d2):
            results.append(_make_match(digits, i, j, y2, m2, d2, "", False))

        # YYMMDD
        y3, m3, d3 = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
        y3 = _expand_year(y3)
        if _valid_date(y3, m3, d3):
            results.append(_make_match(digits, i, j, y3, m3, d3, "", False))

    elif n == 4:
        # MMDD
        m, d = int(digits[0:2]), int(digits[2:4])
        if 1 <= m <= 12 and 1 <= d <= 31:
            results.append(_make_match(digits, i, j, 0, m, d, "", False))

        # DDMM
        d2, m2 = int(digits[0:2]), int(digits[2:4])
        if m2 != m and 1 <= m2 <= 12 and 1 <= d2 <= 31:
            results.append(_make_match(digits, i, j, 0, m2, d2, "", False))

    return results


def _parse_with_separator(
    parts: list[str], sep: str, i: int, j: int, token: str
) -> list[DateMatch]:
    """Parse 3-part date with separator (MM/DD/YYYY etc.)."""
    results: list[DateMatch] = []
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return results

    a, b, c = nums

    # MM/DD/YYYY or DD/MM/YYYY
    if 1900 <= c <= 2099 or (0 <= c <= 99):
        y = c if c >= 100 else _expand_year(c)
        if _valid_date(y, a, b):
            results.append(_make_match(token, i, j, y, a, b, sep, True))
        if a != b and _valid_date(y, b, a):
            results.append(_make_match(token, i, j, y, b, a, sep, True))

    # YYYY/MM/DD
    if 1900 <= a <= 2099:
        if _valid_date(a, b, c):
            results.append(_make_match(token, i, j, a, b, c, sep, True))

    return results


def _parse_with_separator_2part(
    parts: list[str], sep: str, i: int, j: int, token: str
) -> list[DateMatch]:
    """Parse 2-part date with separator (MM/DD etc.)."""
    results: list[DateMatch] = []
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return results

    if 1 <= a <= 12 and 1 <= b <= 31:
        results.append(_make_match(token, i, j, 0, a, b, sep, True))

    return results


def _make_match(
    token: str, i: int, j: int, year: int, month: int, day: int,
    separator: str, has_separator: bool
) -> DateMatch:
    return DateMatch(
        pattern="date",
        token=token,
        i=i,
        j=j,
        year=year,
        month=month,
        day=day,
        separator=separator,
        has_separator=has_separator,
    )


def _valid_date(year: int, month: int, day: int) -> bool:
    """Check if a date is plausibly valid."""
    if year != 0 and not (1900 <= year <= 2099):
        return False
    return 1 <= month <= 12 and 1 <= day <= 31


def _expand_year(two_digit: int) -> int:
    """Expand a 2-digit year to 4 digits using a sliding window."""
    pivot = datetime.date.today().year % 100 + 10
    if two_digit <= pivot:
        return 2000 + two_digit
    return 1900 + two_digit


def _deduplicate(matches: list[DateMatch]) -> list[DateMatch]:
    """Remove duplicate date matches at the same position."""
    seen: set[tuple] = set()
    result: list[DateMatch] = []
    for m in matches:
        key = (m.i, m.j, m.year, m.month, m.day, m.separator)
        if key not in seen:
            seen.add(key)
            result.append(m)
    return result

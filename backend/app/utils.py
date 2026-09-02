"""Phone-number utilities for MTN-momo validation.

A user is considered an MTN subscriber if their phone number, after digit
normalization, matches one of the configured MTN prefixes (after the optional
country code). The prefix list is configurable via app settings.
"""
from __future__ import annotations

from typing import Iterable


def normalize_phone(phone: str | None) -> str:
    """Return only the digits of the phone number.

    Strips spaces, dashes, parentheses, and the leading '+' so that values like
    ``"+27 83 123 4567"`` become ``"27831234567"``.
    """
    if not phone:
        return ""
    return "".join(ch for ch in phone if ch.isdigit())


def _candidate_numbers(digits: str, default_cc: str) -> Iterable[str]:
    """Yield number variants to test, both with and without a default country code."""
    if not digits:
        return []
    candidates = [digits]
    # If the number starts with the default country code, also try without it.
    if default_cc and digits.startswith(default_cc):
        candidates.append(digits[len(default_cc):])
    # If the number does NOT start with the default country code but is short
    # (typical local format), also try with the country code prepended.
    elif default_cc and len(digits) <= 10:
        candidates.append(default_cc + digits)
    return candidates


def is_mtn_number(phone: str | None, prefixes: Iterable[str], default_country_code: str = "27") -> bool:
    """Return True if ``phone`` matches any of the configured MTN prefixes."""
    digits = normalize_phone(phone)
    if not digits:
        return False

    cleaned_prefixes = [p for p in (p.strip() for p in prefixes) if p]
    if not cleaned_prefixes:
        return False

    for candidate in _candidate_numbers(digits, default_country_code):
        for prefix in cleaned_prefixes:
            if candidate.startswith(prefix):
                return True
    return False
"""
status.py

Utility functions for date parsing, tender status evaluation, days left calculation,
and human-friendly date formatting.
"""

from datetime import datetime
import re

SUPPORTED_DATE_FORMATS = [
    # ISO 8601 formats (must be first so YYYY-MM-DD is never parsed with dayfirst=True)
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d %b %Y %I:%M %p",
    "%d %B %Y %I:%M %p",
    "%d %b %Y %H:%M",
    "%d %B %Y %H:%M",
    "%d %b %Y",
    "%d %B %Y",
    "%d/%m/%Y %I:%M %p",
    "%d-%m-%Y %I:%M %p",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
]


def parse_date(date_str):
    """
    Parse a date string across various Indian tender portal formats (ISO, DD/MM/YYYY, etc.).
    Returns a datetime object or None if unparseable.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.strip()
    if not cleaned or cleaned in ("-", "N/A", "NA"):
        return None

    # Handle standard ISO-8601 with or without 'Z'
    if "T" in cleaned:
        try:
            iso_cleaned = cleaned.replace("Z", "+00:00") if cleaned.endswith("Z") else cleaned
            return datetime.fromisoformat(iso_cleaned)
        except Exception:
            pass

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    # Fallback to dateutil parser
    try:
        from dateutil import parser
        # If year is first (e.g. 2026-11-09), dayfirst MUST be False
        is_year_first = bool(re.match(r"^\d{4}[-/]", cleaned))
        return parser.parse(cleaned, dayfirst=not is_year_first)
    except Exception:
        return None


def format_display_date(date_val):
    """
    Format any date string into a user-friendly format:
    e.g. '09-Nov-2026 07:00 PM' or '09-Nov-2026' (if no time specified).
    """
    if not date_val or date_val in ("-", "N/A", "NA"):
        return "-"

    if isinstance(date_val, datetime):
        dt = date_val
    else:
        dt = parse_date(str(date_val))

    if dt is None:
        return str(date_val).strip()

    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
        return dt.strftime("%d-%b-%Y")
    return dt.strftime("%d-%b-%Y %I:%M %p")


def get_status(closing_date):
    """
    Determine if a tender is Active or Expired, and compute days remaining.
    Returns (status: str, days_left: int | None).
    """
    dt = parse_date(closing_date)
    if dt is None:
        return "Unknown", None

    today = datetime.now().date()
    days_left = (dt.date() - today).days

    if days_left < 0:
        return "Expired", days_left

    return "Active", days_left

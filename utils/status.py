"""
status.py

Utility functions for date parsing, tender status evaluation, and days left calculation.
"""

from datetime import datetime

SUPPORTED_DATE_FORMATS = [
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
    Parse a date string across various Indian tender portal formats.
    Returns a datetime object or None if unparseable.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.strip()
    if not cleaned or cleaned in ("-", "N/A", "NA"):
        return None

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    # Fallback to dateutil parser if explicit formats did not match
    try:
        from dateutil import parser
        return parser.parse(cleaned, dayfirst=True)
    except Exception:
        return None


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
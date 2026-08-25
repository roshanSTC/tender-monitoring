
from datetime import datetime
from typing import Optional

from config import logger


DATE_FORMATS = [
    # YYYY-MM-DD
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",

    # DD-MM-YYYY
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y",

    # DD/MM/YYYY
    "%d/%m/%Y %I:%M%p",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",

    # MM/DD/YYYY
    "%m/%d/%Y %I:%M%p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",

    # Month names
    "%d %b %Y %I:%M %p",
    "%d %b %Y %H:%M",
    "%d %b %Y",

    "%d %B %Y %I:%M %p",
    "%d %B %Y %H:%M",
    "%d %B %Y",

    # Month names with hyphen
    "%d-%b-%Y %I:%M %p",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y",

    "%d-%B-%Y %I:%M %p",
    "%d-%B-%Y %H:%M",
    "%d-%B-%Y",
    "%d/%b/%Y %I:%M %p",
]


def parse_tender_date(
    value,
    *,
    log_invalid: bool = True
) -> Optional[datetime]:
    """
    Parse a tender date from a scraper value.

    Returns:
        datetime if parsing succeeds.
        None if value is empty or unsupported.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    if not value:
        return None

    # Normalize repeated whitespace.
    value = " ".join(value.split())

    for date_format in DATE_FORMATS:

        try:
            return datetime.strptime(
                value,
                date_format
            )

        except ValueError:
            continue

    if log_invalid:

        logger.warning(
            "Unsupported tender date format: '%s'",
            value
        )

    return None


def normalize_tender_date(value) -> Optional[str]:
    """
    Normalize a scraper date into:

        YYYY-MM-DD HH:MM:SS

    Returns:
        normalized string or None
    """

    parsed = parse_tender_date(value)

    if parsed is None:
        return None

    return parsed.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

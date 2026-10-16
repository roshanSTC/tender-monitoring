"""
active_tenders.py

Calculates count of active vs expired tenders across all supported portal date formats.
"""

from datetime import datetime
from utils.status import parse_date


def count_active_tenders(tenders):
    """
    Count active and expired tenders based on their closing date.
    Returns (active: int, expired: int).
    """
    active = 0
    expired = 0
    today = datetime.now().date()

    for tender in tenders:
        closing_date = tender.get("Closing Date", "")
        dt = parse_date(closing_date)

        if not dt:
            continue

        if dt.date() >= today:
            active += 1
        else:
            expired += 1

    return active, expired

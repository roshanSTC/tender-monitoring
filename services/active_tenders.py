from datetime import datetime


DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",

    "%d %b %Y %I:%M %p",
    "%d %b %Y %I:%M %p",

    "%d/%m/%Y %I:%M%p",
    "%d/%m/%Y %I:%M %p",

    "%m/%d/%Y %I:%M%p",
    "%m/%d/%Y %I:%M %p",

    "%d %b %Y",
]


def parse_closing_date(value):

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    for date_format in DATE_FORMATS:

        try:
            return datetime.strptime(
                value,
                date_format
            )

        except ValueError:
            continue

    return None


def count_active_tenders(tenders):

    active = 0
    expired = 0

    now = datetime.now()

    for tender in tenders:

        closing_date = parse_closing_date(
            tender.get("Closing Date")
        )

        if closing_date is None:
            continue

        if closing_date >= now:
            active += 1
        else:
            expired += 1

    return active, expired
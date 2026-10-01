from utils.date_utils import parse_tender_date, normalize_tender_date


test_dates = [
    "2025-09-09 17:33:00",
    "09/03/2026 10:00am",
    "10 Aug 2026 11:00 AM",
    "20 Jul 2026 02:00 PM",
    "2025-06-13 15:00:00",
    "2025-12-09 15:00:00",
    "10-Aug-2026 11:00 AM",
    "invalid-date",
]


for value in test_dates:

    parsed = parse_tender_date(value)

    normalized = normalize_tender_date(value)

    print(
        f"{value} -> {parsed} -> {normalized}"
    )
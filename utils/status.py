from datetime import datetime


def get_status(closing_date):

    try:
        closing = datetime.strptime(
            closing_date[:10],
            "%Y-%m-%d"
        ).date()

        today = datetime.today().date()

        days_left = (closing - today).days

        if days_left < 0:
            return "Expired", 0

        return "Active", days_left

    except Exception:
        return "Unknown", 0
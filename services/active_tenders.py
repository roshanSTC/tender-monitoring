from datetime import datetime


def count_active_tenders(tenders):

            active = 0
            expired = 0

            today = datetime.now().date()

            for tender in tenders:

                closing_date = tender.get("Closing Date", "").strip()

                if not closing_date:
                    continue

                try:
                    closing = datetime.strptime(
                        closing_date,
                        "%d %b %Y %I:%M %p"
                    ).date()

                    if closing >= today:
                        active += 1
                    else:
                        expired += 1

                except ValueError:
                    continue

            return active, expired

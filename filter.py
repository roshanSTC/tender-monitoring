"""
filter.py

Filters tenders based on keywords.
"""

from config import KEYWORDS, logger


class TenderFilter:

    def __init__(self):
        self.keywords = [k.lower() for k in KEYWORDS]

    def filter_by_title(self, tenders):

        matched = []

        for tender in tenders:

            title = tender["Tender Title"].lower()

            for keyword in self.keywords:

                if keyword in title:

                    tender["Matched Keyword"] = keyword

                    matched.append(tender)

                    logger.info(
                        f"Matched '{keyword}' -> {tender['Tender Number']}"
                    )

                    break

        logger.info(
            f"{len(matched)} tenders matched keywords."
        )

        return matched
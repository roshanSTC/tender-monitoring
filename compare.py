"""
compare.py

Compares scraped tenders with existing tenders.
"""

from config import logger


class TenderComparer:

    def __init__(self, existing_tenders):

        self.existing_tenders = existing_tenders

    def get_new_tenders(self, scraped_tenders):

        new_tenders = []

        for tender in scraped_tenders:

            source = tender.get("Source", "").strip()

            tender_no = tender.get(
                "Tender Number",
                ""
            ).strip()

            if not tender_no:

                logger.warning(
                    "Tender Number missing."
                )

                continue

            unique_key = f"{source}|{tender_no}"

            if unique_key in self.existing_tenders:

                logger.info(
                    f"Already exists : {unique_key}"
                )

                continue

            new_tenders.append(tender)

        logger.info(
            f"New Tenders : {len(new_tenders)}"
        )

        return new_tenders
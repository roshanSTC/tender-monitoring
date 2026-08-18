"""
compare.py

Compares scraped tenders with database tenders.
"""

from config import logger
from utils.normalizer import TenderNormalizer

class TenderComparer:

    def __init__(self, existing_tenders):

        self.existing_tenders = existing_tenders

    # ----------------------------------------------------------

    def get_changes(self, scraped_tenders):

        new_tenders = []

        updated_tenders = []

        corrigendums = []

        unchanged = []

        for scraped in scraped_tenders:

            source = (
                scraped.get("Source", "")
                or ""
            ).strip()

            tender_no = (
                scraped.get("Tender Number", "")
                or ""
            ).strip()

            if not tender_no:

                logger.warning(
                    "Tender Number missing."
                )

                continue

            unique_key = f"{source}|{tender_no}"

            existing = self.existing_tenders.get(
                unique_key
            )

            # ==============================================
            # NEW TENDER
            # ==============================================

            if existing is None:

                new_tenders.append(
                    scraped
                )

                continue

            # ==============================================
            # COMPARE
            # ==============================================

            changes = self.compare_fields(
                existing,
                scraped,
            )

            # ==============================================
            # NO CHANGE
            # ==============================================

            if not changes:

                unchanged.append(
                    scraped
                )

                continue

            # ==============================================
            # UPDATED TENDER
            # ==============================================

            updated_tenders.append({

                "existing": existing,

                "scraped": scraped,

                "changes": changes,

            })

            # ==============================================
            # CORRIGENDUM
            # ==============================================

            if self.detect_corrigendum(
                existing,
                scraped,
                changes,
            ):

                corrigendums.append({

                    "existing": existing,

                    "scraped": scraped,

                    "changes": changes,

                })

        logger.info(
            f"New Tenders : {len(new_tenders)}"
        )

        logger.info(
            f"Updated : {len(updated_tenders)}"
        )

        logger.info(
            f"Corrigendums : {len(corrigendums)}"
        )

        logger.info(
            f"Unchanged : {len(unchanged)}"
        )

        return {

            "new_tenders": new_tenders,

            "updated_tenders": updated_tenders,

            "corrigendums": corrigendums,

            "unchanged": unchanged,

        }
    
    # ----------------------------------------------------------

    def compare_fields(
        self,
        existing,
        scraped,
    ):

        changes = {}

        # ------------------------------------
        # Title
        # ------------------------------------

        db_title = TenderNormalizer.text(existing.title)

        new_title = TenderNormalizer.text(
            scraped.get("Tender Title")
        )

        if db_title != new_title:

            changes["title"] = {

                "old": existing.title,

                "new": scraped.get("Tender Title"),

            }

        # ------------------------------------
        # Closing Date
        # ------------------------------------

        db_date = TenderNormalizer.date(
            existing.closing_date
        )

        new_date = TenderNormalizer.date(
            scraped.get("Closing Date")
        )

        if db_date != new_date:

            changes["closing_date"] = {

                "old": existing.closing_date,

                "new": scraped.get("Closing Date"),

            }

        # ------------------------------------
        # Tender URL
        # ------------------------------------

        db_url = TenderNormalizer.url(
            existing.tender_url
        )

        new_url = TenderNormalizer.url(
            scraped.get("Tender URL")
        )

        if db_url != new_url:

            changes["tender_url"] = {

                "old": existing.tender_url,

                "new": scraped.get("Tender URL"),

            }

        # ------------------------------------
        # Corrigendum
        # ------------------------------------

        db_corr = TenderNormalizer.text(
            existing.corrigendum
        )

        new_corr = TenderNormalizer.text(
            scraped.get("Corrigendum")
        )

        if db_corr != new_corr:

            changes["corrigendum"] = {

                "old": existing.corrigendum,

                "new": scraped.get("Corrigendum"),

            }
        # ------------------------------------
        # Corrigendum URL
        # ------------------------------------

        db_corr_url = TenderNormalizer.url(
            existing.corrigendum_url
        )

        new_corr_url = TenderNormalizer.url(
            scraped.get("Corrigendum URL")
        )

        if db_corr_url != new_corr_url:

            changes["corrigendum_url"] = {

                "old": existing.corrigendum_url,

                "new": scraped.get("Corrigendum URL"),

            }

    # ----------------------------------------------------------

    def detect_corrigendum(
        self,
        existing,
        scraped,
        changes=None,
    ):
        """
        Detect whether the scraped tender contains
        a new or changed corrigendum.

        A corrigendum can be detected through:

        1. Corrigendum text
        2. Corrigendum URL
        3. Closing-date change associated with a corrigendum
        """

        # ==================================================
        # CURRENT SCRAPED CORRIGENDUM
        # ==================================================

        current_corrigendum = (
            scraped.get(
                "Corrigendum",
                "",
            )
            or ""
        ).strip()

        current_corrigendum_url = (
            scraped.get(
                "Corrigendum URL",
                "",
            )
            or ""
        ).strip()

        # ==================================================
        # EXISTING CORRIGENDUM
        # ==================================================

        existing_corrigendum = (
            existing.corrigendum
            or ""
        ).strip()

        existing_corrigendum_url = (
            existing.corrigendum_url
            or ""
        ).strip()

        # ==================================================
        # NEW CORRIGENDUM TEXT
        # ==================================================

        if (
            current_corrigendum
            and current_corrigendum
            != existing_corrigendum
        ):
            return True

        # ==================================================
        # NEW CORRIGENDUM URL
        # ==================================================

        if (
            current_corrigendum_url
            and current_corrigendum_url
            != existing_corrigendum_url
        ):
            return True

        # ==================================================
        # CLOSING DATE CHANGE
        #
        # A tender closing-date change should also be
        # considered a corrigendum when corrigendum
        # information exists.
        # ==================================================

        if changes:

            closing_change = changes.get(
                "closing_date"
            )

            if closing_change:

                if (
                    current_corrigendum
                    or current_corrigendum_url
                ):
                    return True

        return False
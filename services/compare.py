"""
compare.py

Compares scraped tenders with database tenders.

Responsibilities:
1. Detect new tenders
2. Detect changed tenders
3. Detect possible corrigendum-related changes

IMPORTANT:
This class only DETECTS changes.

It does NOT decide whether a corrigendum history record
is actually new.

The final duplicate check is performed against the
TenderCorrigendum table inside TenderSyncService.
"""

from config import logger
from utils.normalizer import TenderNormalizer


class TenderComparer:

    def __init__(self, existing_tenders):
        self.existing_tenders = existing_tenders

    # ==========================================================
    # MAIN COMPARISON
    # ==========================================================

    def get_changes(self, scraped_tenders):

        new_tenders = []
        updated_tenders = []
        corrigendums = []
        unchanged = []

        for scraped in scraped_tenders:

            source = (
                scraped.get("Source") or ""
            ).strip()

            tender_no = (
                scraped.get("Tender Number") or ""
            ).strip()

            # --------------------------------------------------
            # Invalid tender
            # --------------------------------------------------

            if not source or not tender_no:

                logger.warning(
                    "Source or Tender Number missing."
                )

                continue

            unique_key = (
                f"{source}|{tender_no}"
            )

            existing = self.existing_tenders.get(
                unique_key
            )

            # ==================================================
            # NEW TENDER
            # ==================================================

            if existing is None:

                new_tenders.append(
                    scraped
                )

                continue

            # ==================================================
            # COMPARE EXISTING TENDER
            # ==================================================

            changes = self.compare_fields(
                existing,
                scraped,
            )

            # ==================================================
            # NO CHANGE
            # ==================================================

            if not changes:

                unchanged.append(
                    scraped
                )

                continue

            # ==================================================
            # UPDATED TENDER
            # ==================================================

            update_data = {

                "existing": existing,

                "scraped": scraped,

                "changes": changes,

            }

            updated_tenders.append(
                update_data
            )

            # ==================================================
            # POSSIBLE CORRIGENDUM
            # ==================================================
            #
            # This is only a candidate.
            #
            # TenderSyncService performs the actual database
            # duplicate check before creating history/notification.
            # ==================================================

            if self.detect_corrigendum(
                existing,
                scraped,
                changes,
            ):

                corrigendums.append(
                    update_data
                )

        # ======================================================
        # LOGGING
        # ======================================================

        logger.info(
            f"New Tenders : {len(new_tenders)}"
        )

        logger.info(
            f"Updated : {len(updated_tenders)}"
        )

        logger.info(
            f"Corrigendum Candidates : "
            f"{len(corrigendums)}"
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

    # ==========================================================
    # COMPARE FIELDS
    # ==========================================================

    def compare_fields(
        self,
        existing,
        scraped,
    ):

        changes = {}

        # ======================================================
        # TITLE
        # ======================================================

        db_title = TenderNormalizer.text(
            existing.title
        )

        new_title = TenderNormalizer.text(
            scraped.get("Tender Title")
        )

        if db_title != new_title:

            changes["title"] = {

                "old": existing.title,

                "new": scraped.get(
                    "Tender Title"
                ),

            }

        # ======================================================
        # CLOSING DATE
        # ======================================================

        db_date = TenderNormalizer.date(
            existing.closing_date
        )

        new_date = TenderNormalizer.date(
            scraped.get("Closing Date")
        )

        if db_date != new_date:

            changes["closing_date"] = {

                "old": existing.closing_date,

                "new": scraped.get(
                    "Closing Date"
                ),

            }

        # ======================================================
        # TENDER URL
        # ======================================================

        db_url = TenderNormalizer.url(
            existing.tender_url
        )

        new_url = TenderNormalizer.url(
            scraped.get("Tender URL")
        )

        if db_url != new_url:

            changes["tender_url"] = {

                "old": existing.tender_url,

                "new": scraped.get(
                    "Tender URL"
                ),

            }

        # ======================================================
        # CORRIGENDUM TEXT
        # ======================================================

        db_corr = TenderNormalizer.text(
            existing.corrigendum
        )

        new_corr = TenderNormalizer.text(
            scraped.get("Corrigendum")
        )

        if db_corr != new_corr:

            changes["corrigendum"] = {

                "old": existing.corrigendum,

                "new": scraped.get(
                    "Corrigendum"
                ),

            }

        # ======================================================
        # CORRIGENDUM URL
        # ======================================================

        db_corr_url = TenderNormalizer.url(
            existing.corrigendum_url
        )

        new_corr_url = TenderNormalizer.url(
            scraped.get("Corrigendum URL")
        )

        if db_corr_url != new_corr_url:

            changes["corrigendum_url"] = {

                "old": existing.corrigendum_url,

                "new": scraped.get(
                    "Corrigendum URL"
                ),

            }

        return changes

    # ==========================================================
    # DETECT POSSIBLE CORRIGENDUM
    # ==========================================================

    def detect_corrigendum(
        self,
        existing,
        scraped,
        changes=None,
    ):
        """
        Detect whether an updated tender MAY represent
        a corrigendum.

        IMPORTANT:

        This method does NOT query the corrigendums table.

        It only identifies a possible corrigendum based on
        the scraped tender data.

        TenderSyncService performs the final duplicate check.
        """

        if not changes:
            return False

        # ------------------------------------------------------
        # Current scraped corrigendum data
        # ------------------------------------------------------

        current_corrigendum = TenderNormalizer.text(
            scraped.get("Corrigendum")
        )

        current_corrigendum_url = TenderNormalizer.url(
            scraped.get("Corrigendum URL")
        )

        # ------------------------------------------------------
        # Existing parent tender corrigendum data
        # ------------------------------------------------------

        existing_corrigendum = TenderNormalizer.text(
            existing.corrigendum
        )

        existing_corrigendum_url = TenderNormalizer.url(
            existing.corrigendum_url
        )

        # ======================================================
        # NEW CORRIGENDUM URL
        # ======================================================

        if (
            current_corrigendum_url
            and
            current_corrigendum_url
            != existing_corrigendum_url
        ):

            return True

        # ======================================================
        # NEW CORRIGENDUM TEXT
        # ======================================================

        if (
            current_corrigendum
            and
            current_corrigendum
            != existing_corrigendum
        ):

            return True

        # ======================================================
        # CLOSING DATE CHANGE
        # ======================================================
        #
        # A closing date change is considered a corrigendum
        # candidate only when the scraped tender contains
        # corrigendum information.
        #
        # Final duplicate detection is handled by
        # TenderSyncService against corrigendums.document_url.
        # ======================================================

        if "closing_date" in changes:

            if (
                current_corrigendum_url
                or current_corrigendum
            ):

                return True

        # ======================================================
        # CORRIGENDUM FIELD CHANGED
        # ======================================================

        if "corrigendum" in changes:

            new_corr = TenderNormalizer.text(
                scraped.get("Corrigendum")
            )

            old_corr = TenderNormalizer.text(
                existing.corrigendum
            )

            if new_corr and new_corr != old_corr:
                return True

        if "corrigendum_url" in changes:

            new_url = TenderNormalizer.url(
                scraped.get("Corrigendum URL")
            )

            old_url = TenderNormalizer.url(
                existing.corrigendum_url
            )

            if new_url and new_url != old_url:
                return True

        return False
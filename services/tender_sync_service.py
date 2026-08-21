"""
tender_sync_service.py

Business Orchestrator

Responsibilities

1. Load existing tenders
2. Compare scraped tenders
3. Insert new tenders
4. Update existing tenders
5. Detect corrigendums
6. Backfill historical corrigendums
7. Run corrigendum intelligence
8. Commit everything as a single transaction
"""

from datetime import datetime

from config import logger

from services.compare import TenderComparer

from services.corrigendum_service import (
    CorrigendumService,
)

from services.corrigendum_notification_service import (
    CorrigendumNotificationService,
)

from services.tender_service import (
    get_existing_tenders,
    save_new_tenders,
    update_tender,
)

from services.corrigendum_intelligence import (
    CorrigendumIntelligence,
)

from utils.json_utils import make_json_serializable
from utils.normalizer import TenderNormalizer


class TenderSyncService:

    # ==========================================================
    # MAIN SYNC
    # ==========================================================

    @staticmethod
    def sync(db, scraped_tenders):

        try:

            logger.info(
                "Loading existing tenders..."
            )

            existing_tenders = get_existing_tenders(db)

            logger.info(
                f"Existing : {len(existing_tenders)}"
            )

            # ==================================================
            # COMPARE
            # ==================================================

            logger.info(
                "Comparing tenders..."
            )

            comparer = TenderComparer(
                existing_tenders
            )

            comparison = comparer.get_changes(
                scraped_tenders
            )

            # ==================================================
            # INSERT NEW TENDERS
            # ==================================================

            logger.info(
                "Saving new tenders..."
            )

            inserted = save_new_tenders(
                db=db,
                scraped_tenders=comparison[
                    "new_tenders"
                ],
            )

            logger.info(
                f"Inserted : {len(inserted)}"
            )

            # ==================================================
            # UPDATE EXISTING TENDERS
            # ==================================================

            logger.info(
                "Updating tenders..."
            )

            updated_count = 0

            updated_results = []

            # --------------------------------------------------
            # Process changed tenders
            # --------------------------------------------------

            for update in comparison[
                "updated_tenders"
            ]:

                existing = update[
                    "existing"
                ]

                scraped = update[
                    "scraped"
                ]

                changes = update[
                    "changes"
                ]

                # --------------------------------------------------
                # IMPORTANT
                #
                # The OLD closing date always comes from
                # the existing tender record in the database.
                #
                # We capture it BEFORE update_tender().
                # --------------------------------------------------

                old_closing_date = (
                    TenderNormalizer.date(
                        existing.closing_date
                    )
                )

                logger.info(
                    "Captured OLD closing date from tender table: "
                    f"{existing.source}|"
                    f"{existing.tender_number}|"
                    f"{old_closing_date}"
                )

                # --------------------------------------------------
                # Corrigendum detection
                # --------------------------------------------------

                if TenderSyncService.has_corrigendum(
                    scraped,
                    changes,
                ):

                    logger.info(
                        "Corrigendum detected for "
                        f"{existing.source}|"
                        f"{existing.tender_number}|"
                        f"old_closing_date="
                        f"{old_closing_date}|"
                        f"scraped_closing_date="
                        f"{scraped.get('Closing Date')}"
                    )

                    corrigendum = (
                        TenderSyncService.process_corrigendum(
                            db=db,
                            tender=existing,
                            scraped=scraped,
                            changes=changes,
                            old_closing_date=old_closing_date,
                        )
                    )

                    if corrigendum:

                        logger.info(
                            "Corrigendum created for "
                            f"{existing.source}|"
                            f"{existing.tender_number}|"
                            f"old_closing_date="
                            f"{old_closing_date}"
                        )

                        notification_results = (
                            CorrigendumNotificationService.notify(
                                db=db,
                                tender=existing,
                                corrigendum=corrigendum,
                            )
                        )

                        logger.info(
                            "Corrigendum notifications processed: "
                            f"{len(notification_results)}"
                        )

                # --------------------------------------------------
                # Update tender AFTER corrigendum processing
                # --------------------------------------------------

                update_tender(
                    db,
                    existing,
                    scraped,
                )

                updated_count += 1

                # --------------------------------------------------
                # Store update result
                # --------------------------------------------------

                updated_results.append({
                    "existing": existing,
                    "scraped": scraped,
                    "changes": changes,
                })

            # ==================================================
            # HISTORICAL CORRIGENDUM BACKFILL
            # ==================================================

            logger.info(
                "Checking historical corrigendums..."
            )

            backfilled_count = 0

            for scraped in scraped_tenders:

                source = (
                    scraped.get("Source")
                    or ""
                ).strip()

                tender_number = (
                    scraped.get("Tender Number")
                    or ""
                ).strip()

                if not source or not tender_number:
                    continue

                key = (
                    f"{source}|{tender_number}"
                )

                existing = existing_tenders.get(key)

                if existing is None:
                    continue

                # --------------------------------------------------
                # Corrigendum information
                # --------------------------------------------------

                corrigendum_url = (
                    scraped.get("Corrigendum URL")
                    or ""
                ).strip()

                if not corrigendum_url:
                    continue

                # --------------------------------------------------
                # Check if history already exists
                # --------------------------------------------------

                existing_corrigendum = (
                    CorrigendumService.get_by_document_url(
                        db=db,
                        tender_id=existing.id,
                        document_url=corrigendum_url,
                    )
                )

                if existing_corrigendum:

                    # --------------------------------------------------
                    # Repair missing old/new dates if necessary.
                    #
                    # OLD date comes from tender table.
                    # --------------------------------------------------

                    repaired = False

                    if (
                        existing_corrigendum.old_closing_date
                        is None
                    ):

                        tender_old_date = (
                            TenderNormalizer.date(
                                existing.closing_date
                            )
                        )

                        if tender_old_date:

                            existing_corrigendum.old_closing_date = (
                                tender_old_date
                            )

                            repaired = True

                            logger.info(
                                "Repaired corrigendum OLD closing date "
                                "from tender table: "
                                f"{source}|"
                                f"{tender_number}|"
                                f"{tender_old_date}"
                            )

                    # --------------------------------------------------
                    # Repair NEW closing date from scraped tender
                    # --------------------------------------------------

                    if (
                        existing_corrigendum.new_closing_date
                        is None
                    ):

                        scraped_new_date = (
                            TenderNormalizer.date(
                                scraped.get(
                                    "Closing Date"
                                )
                            )
                        )

                        if scraped_new_date:

                            existing_corrigendum.new_closing_date = (
                                scraped_new_date
                            )

                            repaired = True

                            logger.info(
                                "Repaired corrigendum NEW closing date "
                                f"from scraped data: "
                                f"{source}|"
                                f"{tender_number}|"
                                f"{scraped_new_date}"
                            )

                    if repaired:

                        logger.info(
                            "Existing corrigendum repaired: "
                            f"{source}|"
                            f"{tender_number}|"
                            f"{corrigendum_url}"
                        )

                    continue

                # --------------------------------------------------
                # Historical corrigendum found
                # --------------------------------------------------

                logger.info(
                    "Backfilling historical corrigendum: "
                    f"{source}|{tender_number}"
                )

                # ==================================================
                # IMPORTANT
                #
                # OLD closing date MUST come from the tender table.
                #
                # This is captured BEFORE modifying the tender.
                # ==================================================

                old_closing_date = (
                    TenderNormalizer.date(
                        existing.closing_date
                    )
                )

                # --------------------------------------------------
                # NEW closing date comes from scraped data
                # --------------------------------------------------

                new_closing_date = (
                    TenderNormalizer.date(
                        scraped.get("Closing Date")
                    )
                )

                logger.info(
                    "Historical corrigendum dates: "
                    f"{source}|"
                    f"{tender_number}|"
                    f"old={old_closing_date}|"
                    f"new={new_closing_date}"
                )

                # --------------------------------------------------
                # Build historical changes
                # --------------------------------------------------

                historical_changes = {}

                # Only create a closing-date change when
                # scraped data actually contains a new date.

                if new_closing_date:

                    historical_changes[
                        "closing_date"
                    ] = {

                        "old": old_closing_date,

                        "new": new_closing_date,

                    }

                # ==================================================
                # Create corrigendum FIRST
                # ==================================================

                logger.info(
                    "Creating historical corrigendum with "
                    f"old_closing_date={old_closing_date}|"
                    f"new_closing_date={new_closing_date}"
                )

                corrigendum = (
                    TenderSyncService.process_corrigendum(

                        db=db,

                        tender=existing,

                        scraped=scraped,

                        changes=historical_changes,

                        old_closing_date=old_closing_date,

                    )
                )

                # ==================================================
                # Update parent tender AFTER corrigendum history
                # ==================================================

                if new_closing_date:

                    normalized_existing_date = (
                        TenderNormalizer.date(
                            existing.closing_date
                        )
                    )

                    if (
                        normalized_existing_date
                        != new_closing_date
                    ):

                        existing.closing_date = (
                            new_closing_date
                        )

                        existing.updated_at = (
                            datetime.utcnow()
                        )

                        logger.info(
                            "Updated tender closing date from "
                            "historical corrigendum: "
                            f"{source}|"
                            f"{tender_number}|"
                            f"{new_closing_date}"
                        )

                # --------------------------------------------------
                # Count
                # --------------------------------------------------

                if corrigendum:

                    backfilled_count += 1

                    notification_results = (
                        CorrigendumNotificationService.notify(
                            db=db,
                            tender=existing,
                            corrigendum=corrigendum,
                        )
                    )

                    logger.info(
                        "Historical corrigendum "
                        "notifications processed: "
                        f"{len(notification_results)}"
                    )

            logger.info(
                "Historical Corrigendums Backfilled : "
                f"{backfilled_count}"
            )

            # ==================================================
            # COMMIT
            # ==================================================

            db.commit()

            logger.info(
                "Tender synchronization completed."
            )

            # ==================================================
            # SUMMARY
            # ==================================================

            corrigendum_count = (
                len(
                    comparison[
                        "corrigendums"
                    ]
                )
                + backfilled_count
            )

            logger.info(
                f"New : "
                f"{len(comparison['new_tenders'])}"
            )

            logger.info(
                f"Updated : "
                f"{updated_count}"
            )

            logger.info(
                f"Corrigendums : "
                f"{corrigendum_count}"
            )

            logger.info(
                f"Unchanged : "
                f"{len(comparison['unchanged'])}"
            )

            return {

                "success": True,

                "summary": {

                    "new_tenders": len(
                        comparison[
                            "new_tenders"
                        ]
                    ),

                    "updated_tenders": (
                        updated_count
                    ),

                    "corrigendums": (
                        corrigendum_count
                    ),

                    "unchanged": len(
                        comparison[
                            "unchanged"
                        ]
                    ),

                    "backfilled_corrigendums": (
                        backfilled_count
                    ),

                },

                "inserted": inserted,

                "updated": updated_results,

                "corrigendums": comparison[
                    "corrigendums"
                ],

            }

        except Exception as e:

            logger.exception(
                "Tender synchronization failed."
            )

            db.rollback()

            raise

    # ==========================================================
    # CHECK CORRIGENDUM
    # ==========================================================

    @staticmethod
    def has_corrigendum(
        scraped,
        changes,
    ):
        """
        Determines whether the current scrape
        contains a corrigendum.
        """

        corrigendum = (
            scraped.get("Corrigendum")
            or ""
        ).strip()

        corrigendum_url = (
            scraped.get("Corrigendum URL")
            or ""
        ).strip()

        if corrigendum_url:
            return True

        if corrigendum:
            return True

        if (
            "corrigendum" in changes
            or
            "corrigendum_url" in changes
        ):
            return True

        return False

    # ==========================================================
    # PROCESS CORRIGENDUM
    # ==========================================================

    @staticmethod
    def process_corrigendum(
        db,
        tender,
        scraped,
        changes,
        old_closing_date=None,
    ):
        """
        Creates or repairs a corrigendum history record.

        IMPORTANT DATE RULE:

        OLD closing date:
            Always comes from the existing tender table
            before the tender is updated.

        NEW closing date:
            Comes from the scraped tender data.

        The explicit old_closing_date argument is retained
        so the caller can pass the database value captured
        before any update.

        No commit happens here.
        The parent sync transaction controls commit.
        """

        corrigendum_url = (
            scraped.get("Corrigendum URL")
            or ""
        ).strip()

        corrigendum_text = (
            scraped.get("Corrigendum")
            or ""
        ).strip()

        # ------------------------------------------------------
        # Nothing to save
        # ------------------------------------------------------

        if not corrigendum_url:
            return None

        # ------------------------------------------------------
        # IMPORTANT
        #
        # If caller did not explicitly provide old date,
        # get it directly from the tender table.
        # ------------------------------------------------------

        if old_closing_date is None:

            old_closing_date = (
                TenderNormalizer.date(
                    tender.closing_date
                )
            )

        else:

            old_closing_date = (
                TenderNormalizer.date(
                    old_closing_date
                )
            )

        logger.info(
            "Corrigendum OLD closing date from tender table: "
            f"{tender.source}|"
            f"{tender.tender_number}|"
            f"{old_closing_date}"
        )

        # ------------------------------------------------------
        # Prevent duplicates
        # ------------------------------------------------------

        existing_corrigendum = (
            CorrigendumService.get_by_document_url(
                db=db,
                tender_id=tender.id,
                document_url=corrigendum_url,
            )
        )

        if existing_corrigendum:

            repaired = False

            # --------------------------------------------------
            # OLD closing date
            # --------------------------------------------------

            if (
                existing_corrigendum.old_closing_date is None
                and old_closing_date is not None
            ):

                existing_corrigendum.old_closing_date = (
                    old_closing_date
                )

                repaired = True

                logger.info(
                    "Repaired missing OLD closing date: "
                    f"{tender.source}|"
                    f"{tender.tender_number}|"
                    f"{old_closing_date}"
                )

            # --------------------------------------------------
            # NEW closing date
            # --------------------------------------------------

            scraped_new_date = (
                TenderNormalizer.date(
                    scraped.get("Closing Date")
                )
            )

            if (
                scraped_new_date is not None
                and
                existing_corrigendum.new_closing_date
                != scraped_new_date
            ):

                logger.info(
                    "Updating corrigendum NEW closing date: "
                    f"{tender.source}|"
                    f"{tender.tender_number}|"
                    f"old_history="
                    f"{existing_corrigendum.new_closing_date}|"
                    f"new_scraped="
                    f"{scraped_new_date}"
                )

                existing_corrigendum.new_closing_date = (
                    scraped_new_date
                )

                repaired = True

            # --------------------------------------------------
            # Update parent tender closing date as well
            # --------------------------------------------------

            if scraped_new_date is not None:

                current_tender_date = (
                    TenderNormalizer.date(
                        tender.closing_date
                    )
                )

                if current_tender_date != scraped_new_date:

                    tender.closing_date = (
                        scraped_new_date
                    )

                    tender.updated_at = datetime.utcnow()

                    repaired = True

                    logger.info(
                        "Updated tender closing date: "
                        f"{tender.source}|"
                        f"{tender.tender_number}|"
                        f"{current_tender_date}"
                        f" -> "
                        f"{scraped_new_date}"
                    )

            if repaired:

                logger.info(
                    "Existing corrigendum repaired: "
                    f"{tender.source}|"
                    f"{tender.tender_number}|"
                    f"{corrigendum_url}"
                )

            return existing_corrigendum

        # ------------------------------------------------------
        # Intelligence
        # ------------------------------------------------------

        intelligence = make_json_serializable(
            CorrigendumIntelligence.analyze(
                changes
            )
        )

        # ------------------------------------------------------
        # Closing date change
        # ------------------------------------------------------

        closing_change = (
            changes.get(
                "closing_date",
                {}
            )
        )

        new_closing_date = (
            closing_change.get("new")
        )

        # ------------------------------------------------------
        # IMPORTANT
        #
        # Never use changes["old"] as the primary source
        # for the old date.
        #
        # The tender table is the source of truth.
        # ------------------------------------------------------

        if new_closing_date is None:

            new_closing_date = (
                scraped.get(
                    "Closing Date"
                )
            )

        new_closing_date = (
            TenderNormalizer.date(
                new_closing_date
            )
        )

        # ------------------------------------------------------
        # Debug logging
        # ------------------------------------------------------

        logger.info(
            "========== PROCESS CORRIGENDUM =========="
        )

        logger.info(
            "Tender: "
            f"{tender.source}|"
            f"{tender.tender_number}"
        )

        logger.info(
            "Tender DB closing date: "
            f"{tender.closing_date}"
        )

        logger.info(
            "OLD closing date: "
            f"{old_closing_date}"
        )

        logger.info(
            "NEW closing date: "
            f"{new_closing_date}"
        )

        logger.info(
            "Corrigendum URL: "
            f"{corrigendum_url}"
        )

        logger.info(
            "=========================================="
        )

        # ------------------------------------------------------
        # Corrigendum number
        # ------------------------------------------------------

        corrigendum_no = (
            CorrigendumService.generate_corrigendum_no(
                db=db,
                tender_id=tender.id,
                corrigendum_text=corrigendum_text,
                document_url=corrigendum_url,
            )
        )

        # ------------------------------------------------------
        # Create corrigendum history
        # ------------------------------------------------------

        corrigendum = (
            CorrigendumService.create_corrigendum(

                db=db,

                tender_id=tender.id,

                corrigendum_no=corrigendum_no,

                document_url=corrigendum_url,

                title=(
                    scraped.get(
                        "Tender Title"
                    )
                    or tender.title
                ),

                published_date=(
                    scraped.get(
                        "Publishing Date"
                    )
                ),

                # ----------------------------------------------
                # OLD = tender table
                # ----------------------------------------------

                old_closing_date=(
                    old_closing_date
                ),

                # ----------------------------------------------
                # NEW = scraped data
                # ----------------------------------------------

                new_closing_date=(
                    new_closing_date
                ),

                change_summary="\n".join(
                    intelligence[
                        "summary"
                    ]
                ),

                risk_level=(
                    intelligence[
                        "risk_level"
                    ]
                ),

                risk_score=(
                    intelligence[
                        "risk_score"
                    ]
                ),

                categories=(
                    intelligence[
                        "categories"
                    ]
                ),

                detected_changes=(
                    intelligence[
                        "details"
                    ]
                ),
            )
        )

        # ------------------------------------------------------
        # Logging
        # ------------------------------------------------------

        logger.info(
            "Corrigendum processed: "
            f"{tender.source}|"
            f"{tender.tender_number}|"
            f"{corrigendum_no}|"
            f"old_closing_date="
            f"{old_closing_date}|"
            f"new_closing_date="
            f"{new_closing_date}"
        )

        return corrigendum
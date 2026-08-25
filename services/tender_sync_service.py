"""
tender_sync_service.py

Business Orchestrator

Responsibilities

1. Load existing tenders
2. Compare scraped tenders
3. Insert new tenders
4. Update existing tenders
5. Detect corrigendums
6. Prevent duplicate corrigendums
7. Backfill historical corrigendums
8. Run corrigendum intelligence
9. Send notifications only for NEW corrigendums
10. Commit everything as a single transaction
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
    def sync(
        db,
        scraped_tenders,
    ):

        try:

            # ==================================================
            # LOAD EXISTING
            # ==================================================

            logger.info(
                "Loading existing tenders..."
            )

            existing_tenders = (
                get_existing_tenders(db)
            )

            logger.info(
                f"Existing : "
                f"{len(existing_tenders)}"
            )
            
            
            # ==================================================
            # DETECT DUPLICATE SCRAPED TENDERS
            # ==================================================

            logger.info(
                "Checking duplicate scraped tenders..."
            )

            seen_tenders = set()
            unique_scraped_tenders = []
            duplicate_count = 0

            for tender in scraped_tenders:

                source = (
                    tender.get("Source")
                    or ""
                ).strip()

                tender_number = (
                    tender.get("Tender Number")
                    or ""
                ).strip()

                # ----------------------------------------------
                # Skip invalid records
                # ----------------------------------------------

                if not source or not tender_number:

                    unique_scraped_tenders.append(tender)

                    continue

                key = (
                    source,
                    tender_number,
                )

                # ----------------------------------------------
                # Duplicate
                # ----------------------------------------------

                if key in seen_tenders:

                    duplicate_count += 1

                    logger.warning(
                        "Duplicate scraped tender detected: "
                        f"{source}|{tender_number}"
                    )

                    continue

                # ----------------------------------------------
                # First occurrence
                # ----------------------------------------------

                seen_tenders.add(key)

                unique_scraped_tenders.append(tender)


            scraped_tenders = unique_scraped_tenders

            logger.info(
                f"Duplicate scraped tenders removed: "
                f"{duplicate_count}"
            )

            logger.info(
                f"Unique scraped tenders: "
                f"{len(scraped_tenders)}"
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

            comparison = (
                comparer.get_changes(
                    scraped_tenders
                )
            )

            # ==================================================
            # INSERT NEW TENDERS
            # ==================================================

            logger.info(
                "Saving new tenders..."
            )

            inserted = save_new_tenders(
                db=db,
                scraped_tenders=(
                    comparison[
                        "new_tenders"
                    ]
                ),
            )

            logger.info(
                f"Inserted : {len(inserted)}"
            )

            # ==================================================
            # REFRESH EXISTING TENDERS AFTER INSERT
            # ==================================================
            #
            # get_existing_tenders() was loaded before new
            # tenders were inserted.
            #
            # The historical corrigendum backfill later in this
            # sync needs to be able to find newly inserted
            # tenders as well.
            # ==================================================

            if inserted:

                logger.info(
                    "Refreshing existing tenders after insert..."
                )

                existing_tenders = (
                    get_existing_tenders(db)
                )

                logger.info(
                    f"Existing tenders after insert : "
                    f"{len(existing_tenders)}"
                )

            # ==================================================
            # UPDATE EXISTING TENDERS
            # ==================================================

            logger.info(
                "Updating tenders..."
            )

            updated_count = 0

            updated_results = []

            # ==================================================
            # NEW CORRIGENDUM COUNTER
            # ==================================================
            #
            # IMPORTANT:
            #
            # This counts ONLY corrigendums that are actually
            # created in the corrigendums table.
            #
            # It does NOT count:
            #
            # - detected candidates
            # - existing corrigendums
            # - repaired corrigendums
            # ==================================================

            new_corrigendum_count = 0
            
            pre_update_closing_dates = {}

            # ==================================================
            # PROCESS UPDATED TENDERS
            # ==================================================

            for update_data in comparison[
                "updated_tenders"
            ]:

                existing = update_data[
                    "existing"
                ]

                scraped = update_data[
                    "scraped"
                ]

                changes = update_data[
                    "changes"
                ]
                
                logger.info(
                    "============================================================"
                )

                logger.info(
                    f"UPDATED TENDER: "
                    f"{existing.source}|"
                    f"{existing.tender_number}"
                )

                logger.info(
                    f"CHANGES: {changes}"
                )

                logger.info(
                    "============================================================"
                )

                # --------------------------------------------------
                # Capture OLD closing date BEFORE updating tender
                # --------------------------------------------------

                old_closing_date = (
                    TenderNormalizer.date(
                        existing.closing_date
                    )
                )

                logger.info(
                    "Captured OLD closing date: "
                    f"{existing.source}|"
                    f"{existing.tender_number}|"
                    f"{old_closing_date}"
                )
                
                pre_update_closing_dates[existing.id] = (
                    old_closing_date
                )

                # ==================================================
                # CORRIGENDUM DETECTION
                # ==================================================

                if comparer.detect_corrigendum(
                    existing=existing,
                    scraped=scraped,
                    changes=changes,
                ):

                    logger.info(
                        "Corrigendum candidate detected: "
                        f"{existing.source}|"
                        f"{existing.tender_number}"
                    )

                    # --------------------------------------------------
                    # process_corrigendum now returns:
                    #
                    # (corrigendum, created)
                    #
                    # created=True  -> genuinely new
                    # created=False -> already existed
                    # --------------------------------------------------

                    corrigendum, created = (
                        TenderSyncService.process_corrigendum(
                            db=db,
                            tender=existing,
                            scraped=scraped,
                            changes=changes,
                            old_closing_date=old_closing_date,
                        )
                    )

                    # ==================================================
                    # ONLY NEW CORRIGENDUM
                    # ==================================================

                    if (
                        corrigendum
                        and
                        created
                    ):

                        new_corrigendum_count += 1

                        logger.info(
                            "NEW CORRIGENDUM CREATED: "
                            f"{existing.source}|"
                            f"{existing.tender_number}|"
                            f"{corrigendum.corrigendum_no}"
                        )

                        # --------------------------------------------------
                        # SEND NOTIFICATION ONLY ON NEW RECORD
                        # --------------------------------------------------

                        notification_results = (
                            CorrigendumNotificationService.notify(
                                db=db,
                                tender=existing,
                                corrigendum=corrigendum,
                            )
                        )

                        logger.info(
                            "New corrigendum notifications processed: "
                            f"{len(notification_results)}"
                        )

                    elif corrigendum:

                        logger.info(
                            "Existing corrigendum detected. "
                            "Notification skipped: "
                            f"{existing.source}|"
                            f"{existing.tender_number}|"
                            f"{corrigendum.corrigendum_no}"
                        )

                # ==================================================
                # UPDATE PARENT TENDER
                # ==================================================

                update_tender(
                    db=db,
                    tender=existing,
                    scraped=scraped,
                )

                updated_count += 1

                # ==================================================
                # STORE RESULT
                # ==================================================

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
                    scraped.get(
                        "Tender Number"
                    )
                    or ""
                ).strip()

                if (
                    not source
                    or
                    not tender_number
                ):

                    continue

                key = (
                    f"{source}|"
                    f"{tender_number}"
                )

                existing = (
                    existing_tenders.get(
                        key
                    )
                )

                if existing is None:
                    continue

                # ==================================================
                # CORRIGENDUM URL
                # ==================================================

                corrigendum_url = (
                    scraped.get(
                        "Corrigendum URL"
                    )
                    or ""
                ).strip()

                if not corrigendum_url:
                    continue

                # Normalize URL before comparison
                corrigendum_url = (
                    TenderNormalizer.url(
                        corrigendum_url
                    )
                )

                if not corrigendum_url:
                    continue

                # ==================================================
                # CHECK HISTORY
                # ==================================================

                existing_corrigendum = (
                    CorrigendumService.get_by_document_url(
                        db=db,
                        tender_id=existing.id,
                        document_url=corrigendum_url,
                    )
                )

                # ==================================================
                # ALREADY EXISTS
                # ==================================================

                if existing_corrigendum:

                    repaired = False

                    # --------------------------------------------------
                    # Repair OLD closing date
                    # --------------------------------------------------

                    if (
                        existing_corrigendum.old_closing_date
                        is None
                    ):

                        tender_old_date = (
                            pre_update_closing_dates.get(
                                existing.id,
                                TenderNormalizer.date(
                                    existing.closing_date
                                ),
                            )
                        )

                        if tender_old_date:

                            existing_corrigendum.old_closing_date = (
                                tender_old_date
                            )

                            repaired = True

                            logger.info(
                                "Repaired existing corrigendum OLD date: "
                                f"{source}|"
                                f"{tender_number}|"
                                f"{tender_old_date}"
                            )

                    # --------------------------------------------------
                    # Repair NEW closing date
                    # --------------------------------------------------

                    scraped_new_date = (
                        TenderNormalizer.date(
                            scraped.get(
                                "Closing Date"
                            )
                        )
                    )

                    if (
                        existing_corrigendum
                        .new_closing_date
                        is None
                        and
                        scraped_new_date
                    ):

                        existing_corrigendum.new_closing_date = (
                            scraped_new_date
                        )

                        repaired = True

                        logger.info(
                            "Repaired existing corrigendum NEW date: "
                            f"{source}|"
                            f"{tender_number}|"
                            f"{scraped_new_date}"
                        )

                    # --------------------------------------------------
                    # DO NOT NOTIFY
                    # --------------------------------------------------

                    if repaired:

                        logger.info(
                            "Existing corrigendum repaired. "
                            "Notification skipped: "
                            f"{source}|"
                            f"{tender_number}|"
                            f"{corrigendum_url}"
                        )

                    continue

                # ==================================================
                # HISTORICAL CORRIGENDUM FOUND
                # ==================================================

                logger.info(
                    "NEW HISTORICAL CORRIGENDUM FOUND: "
                    f"{source}|"
                    f"{tender_number}|"
                    f"{corrigendum_url}"
                )

                # ==================================================
                # OLD DATE
                # ==================================================

                old_closing_date = (
                    pre_update_closing_dates.get(
                        existing.id,
                        TenderNormalizer.date(
                            existing.closing_date
                        ),
                    )
                )

                # ==================================================
                # NEW DATE
                # ==================================================

                new_closing_date = (
                    TenderNormalizer.date(
                        scraped.get(
                            "Closing Date"
                        )
                    )
                )

                logger.info(
                    "Historical corrigendum dates: "
                    f"{source}|"
                    f"{tender_number}|"
                    f"old={old_closing_date}|"
                    f"new={new_closing_date}"
                )

                # ==================================================
                # BUILD CHANGES
                # ==================================================

                historical_changes = {}

                if new_closing_date:

                    # Only record a change if dates differ
                    if (
                        old_closing_date
                        != new_closing_date
                    ):

                        historical_changes[
                            "closing_date"
                        ] = {

                            "old": old_closing_date,

                            "new": new_closing_date,

                        }

                # ==================================================
                # CREATE HISTORICAL CORRIGENDUM
                # ==================================================

                corrigendum, created = (
                    TenderSyncService.process_corrigendum(
                        db=db,
                        tender=existing,
                        scraped=scraped,
                        changes=historical_changes,
                        old_closing_date=old_closing_date,
                    )
                )

                # ==================================================
                # UPDATE PARENT TENDER
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
                            "Updated tender closing date "
                            "from historical corrigendum: "
                            f"{source}|"
                            f"{tender_number}|"
                            f"{normalized_existing_date}"
                            f" -> "
                            f"{new_closing_date}"
                        )

                # ==================================================
                # ONLY COUNT + NOTIFY IF CREATED
                # ==================================================

                if (
                    corrigendum
                    and
                    created
                ):

                    backfilled_count += 1

                    new_corrigendum_count += 1

                    logger.info(
                        "Historical NEW corrigendum created: "
                        f"{source}|"
                        f"{tender_number}|"
                        f"{corrigendum.corrigendum_no}"
                    )

                    notification_results = (
                        CorrigendumNotificationService.notify(
                            db=db,
                            tender=existing,
                            corrigendum=corrigendum,
                        )
                    )

                    logger.info(
                        "Historical corrigendum notifications "
                        "processed: "
                        f"{len(notification_results)}"
                    )

            # ==================================================
            # BACKFILL SUMMARY
            # ==================================================

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
            # FINAL SUMMARY
            # ==================================================

            logger.info(
                "============================================================"
            )

            logger.info(
                "Synchronization Summary"
            )

            logger.info(
                "============================================================"
            )

            logger.info(
                f"New Tenders     : "
                f"{len(comparison['new_tenders'])}"
            )

            logger.info(
                f"Updated Tenders : "
                f"{updated_count}"
            )

            logger.info(
                f"Corrigendums    : "
                f"{new_corrigendum_count}"
            )

            logger.info(
                f"Unchanged       : "
                f"{len(comparison['unchanged'])}"
            )

            logger.info(
                "============================================================"
            )

            # ==================================================
            # RETURN
            # ==================================================

            return {

                "success": True,

                "summary": {

                    "new_tenders": (
                        len(
                            comparison[
                                "new_tenders"
                            ]
                        )
                    ),

                    "updated_tenders": (
                        updated_count
                    ),

                    "corrigendums_created": (
                        new_corrigendum_count
                    ),

                    "unchanged": (
                        len(
                            comparison[
                                "unchanged"
                            ]
                        )
                    ),

                    "backfilled_corrigendums": (
                        backfilled_count
                    ),

                },

                "inserted": inserted,

                "updated": updated_results,

                "corrigendum_candidates": (
                    comparison[
                        "corrigendums"
                    ]
                ),

            }

        except Exception as e:

            logger.exception(
                "Tender synchronization failed."
            )

            db.rollback()

            raise

    

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

        RETURNS:

            (corrigendum, created)

        Where:

            created=True
                A NEW history record was inserted.

            created=False
                The corrigendum already existed.

        This distinction is critical because notifications
        must only be sent for newly created corrigendums.
        """

        # ======================================================
        # CORRIGENDUM URL
        # ======================================================

        corrigendum_url = TenderNormalizer.url(
            scraped.get(
                "Corrigendum URL"
            )
        )

        corrigendum_text = TenderNormalizer.text(
            scraped.get(
                "Corrigendum"
            )
        )

        # ======================================================
        # NOTHING TO PROCESS
        # ======================================================

        if not corrigendum_url:

            return None, False

        # ======================================================
        # OLD CLOSING DATE
        # ======================================================

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
            "Corrigendum OLD closing date: "
            f"{tender.source}|"
            f"{tender.tender_number}|"
            f"{old_closing_date}"
        )

        # ======================================================
        # DUPLICATE CHECK
        # ======================================================

        existing_corrigendum = (
            CorrigendumService.get_by_document_url(
                db=db,
                tender_id=tender.id,
                document_url=corrigendum_url,
            )
        )

        # ======================================================
        # EXISTING CORRIGENDUM
        # ======================================================

        if existing_corrigendum:

            repaired = False

            # --------------------------------------------------
            # Repair OLD date
            # --------------------------------------------------

            if (
                existing_corrigendum.old_closing_date
                is None
                and
                old_closing_date
                is not None
            ):

                existing_corrigendum.old_closing_date = (
                    old_closing_date
                )

                repaired = True

                logger.info(
                    "Repaired existing corrigendum OLD date: "
                    f"{tender.source}|"
                    f"{tender.tender_number}|"
                    f"{old_closing_date}"
                )

            # --------------------------------------------------
            # Scraped NEW date
            # --------------------------------------------------

            scraped_new_date = (
                TenderNormalizer.date(
                    scraped.get(
                        "Closing Date"
                    )
                )
            )

            # --------------------------------------------------
            # Repair NEW date only when history has no value
            # --------------------------------------------------

            if (
                existing_corrigendum.new_closing_date
                is None
                and
                scraped_new_date
                is not None
            ):

                existing_corrigendum.new_closing_date = (
                    scraped_new_date
                )

                repaired = True

                logger.info(
                    "Repaired existing corrigendum NEW date: "
                    f"{tender.source}|"
                    f"{tender.tender_number}|"
                    f"{scraped_new_date}"
                )

            # --------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT overwrite an existing corrigendum's
            # new_closing_date every time the scraper runs.
            #
            # The history record represents the original
            # corrigendum event.
            # --------------------------------------------------

            # --------------------------------------------------
            # Update parent tender if required
            # --------------------------------------------------

            if scraped_new_date is not None:

                current_tender_date = (
                    TenderNormalizer.date(
                        tender.closing_date
                    )
                )

                if (
                    current_tender_date
                    != scraped_new_date
                ):

                    tender.closing_date = (
                        scraped_new_date
                    )

                    tender.updated_at = (
                        datetime.utcnow()
                    )

                    repaired = True

                    logger.info(
                        "Updated tender closing date "
                        "from existing corrigendum: "
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

            # --------------------------------------------------
            # CRITICAL:
            #
            # Return created=False.
            #
            # Caller MUST NOT send notification.
            # --------------------------------------------------

            return existing_corrigendum, False

        # ======================================================
        # INTELLIGENCE
        # ======================================================

        intelligence = (
            make_json_serializable(
                CorrigendumIntelligence.analyze(
                    changes or {}
                )
            )
        )

        # ======================================================
        # CLOSING DATE CHANGE
        # ======================================================

        closing_change = (
            (changes or {}).get(
                "closing_date",
                {}
            )
        )

        new_closing_date = (
            closing_change.get(
                "new"
            )
        )

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

        # ======================================================
        # DEBUG
        # ======================================================

        logger.info(
            "========== PROCESS NEW CORRIGENDUM =========="
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
            "============================================="
        )

        # ======================================================
        # GENERATE CORRIGENDUM NUMBER
        # ======================================================

        corrigendum_no = (
            CorrigendumService.generate_corrigendum_no(
                db=db,
                tender_id=tender.id,
                corrigendum_text=corrigendum_text,
                document_url=corrigendum_url,
            )
        )

        # ======================================================
        # CREATE HISTORY
        # ======================================================

        corrigendum, created = (
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
                    TenderNormalizer.date(
                        scraped.get(
                            "Publishing Date"
                        )
                    )
                ),

                old_closing_date=(
                    old_closing_date
                ),

                new_closing_date=(
                    new_closing_date
                ),

                change_summary=(
                    "\n".join(
                        intelligence[
                            "summary"
                        ]
                    )
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

        return corrigendum, created
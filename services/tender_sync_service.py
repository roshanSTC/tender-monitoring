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

                # ----------------------------------------------
                # Update tender
                # ----------------------------------------------

                update_tender(
                    db,
                    existing,
                    scraped,
                )

                updated_count += 1

                # ----------------------------------------------
                # Corrigendum detection
                # ----------------------------------------------

                if TenderSyncService.has_corrigendum(
                    scraped,
                    changes,
                ):

                    corrigendum = (
                        TenderSyncService.process_corrigendum(
                            db=db,
                            tender=existing,
                            scraped=scraped,
                            changes=changes,
                        )
                    )

                    if corrigendum:

                        logger.info(
                            "Corrigendum created for "
                            f"{existing.source}|"
                            f"{existing.tender_number}"
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

                # ----------------------------------------------
                # Store update result
                # ----------------------------------------------

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

                existing = existing_tenders.get(
                    key
                )

                # New tenders were already inserted above.
                # Their corrigendum will be checked separately
                # below if necessary.
                if existing is None:
                    continue

                corrigendum_url = (
                    scraped.get(
                        "Corrigendum URL"
                    )
                    or ""
                ).strip()

                corrigendum_text = (
                    scraped.get(
                        "Corrigendum"
                    )
                    or ""
                ).strip()

                # No corrigendum
                if not corrigendum_url:
                    continue

                # ----------------------------------------------
                # Check if history already exists
                # ----------------------------------------------

                existing_corrigendum = (
                    CorrigendumService.get_by_document_url(
                        db=db,
                        tender_id=existing.id,
                        document_url=corrigendum_url,
                    )
                )

                if existing_corrigendum:

                    continue

                # ----------------------------------------------
                # Existing tender has corrigendum but history
                # does not contain it.
                #
                # This is the historical backfill case.
                # ----------------------------------------------

                logger.info(
                    "Backfilling historical corrigendum: "
                    f"{source}|{tender_number}"
                )

                corrigendum = (
                    TenderSyncService.process_corrigendum(
                        db=db,
                        tender=existing,
                        scraped=scraped,
                        changes={},
                    )
                )

                if corrigendum:

                    backfilled_count += 1

            logger.info(
                f"Historical Corrigendums Backfilled : "
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
                len(comparison["corrigendums"])
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
    ):
        """
        Creates a corrigendum history record.

        Intelligence is calculated before storing
        the corrigendum.

        No commit happens here.
        The parent sync transaction controls commit.
        """

        corrigendum_url = (
            scraped.get(
                "Corrigendum URL"
            )
            or ""
        ).strip()

        corrigendum_text = (
            scraped.get(
                "Corrigendum"
            )
            or ""
        ).strip()

        # ------------------------------------------------------
        # Nothing to save
        # ------------------------------------------------------

        if not corrigendum_url:

            return None

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

            logger.info(
                "Corrigendum already exists: "
                f"{tender.source}|"
                f"{tender.tender_number}|"
                f"{corrigendum_url}"
            )

            return None

        # ------------------------------------------------------
        # Intelligence
        # ------------------------------------------------------

        intelligence = (
            CorrigendumIntelligence.analyze(
                changes
            )
        )

        # ------------------------------------------------------
        # Closing dates
        # ------------------------------------------------------

        old_closing_date = (
            changes
            .get(
                "closing_date",
                {}
            )
            .get("old")
        )

        new_closing_date = (
            changes
            .get(
                "closing_date",
                {}
            )
            .get("new")
        )

        # Historical backfill case:
        #
        # There may be no closing-date change in `changes`,
        # so use the tender's current closing date.

        if new_closing_date is None:

            new_closing_date = (
                scraped.get(
                    "Closing Date"
                )
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
        # Create
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

                old_closing_date=(
                    old_closing_date
                ),

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
            f"{corrigendum_no}"
        )

        return corrigendum
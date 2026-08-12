from sqlalchemy.orm import Session

from models.tender_corrigendum import TenderCorrigendum


class CorrigendumService:

    # =========================================================
    # CREATE CORRIGENDUM
    # =========================================================

    @staticmethod
    def create_corrigendum(
        db: Session,
        tender_id: int,
        corrigendum_no: str,
        document_url: str,
        title: str | None = None,
        published_date=None,
        old_closing_date=None,
        new_closing_date=None,
        change_summary=None,
        risk_level=None,
        risk_score=None,
        categories=None,
        detected_changes=None,
    ):
        """
        Create a corrigendum history record.

        IMPORTANT:
        This method does NOT commit.

        TenderSyncService controls the transaction.
        """

        # -----------------------------------------------------
        # Check by corrigendum number
        # -----------------------------------------------------

        exists = (
            db.query(TenderCorrigendum)
            .filter(
                TenderCorrigendum.tender_id == tender_id,
                TenderCorrigendum.corrigendum_no
                == corrigendum_no,
            )
            .first()
        )

        if exists:
            return exists

        # -----------------------------------------------------
        # Check by document URL
        # -----------------------------------------------------

        if document_url:

            exists = (
                db.query(TenderCorrigendum)
                .filter(
                    TenderCorrigendum.tender_id
                    == tender_id,

                    TenderCorrigendum.document_url
                    == document_url,
                )
                .first()
            )

            if exists:
                return exists

        # -----------------------------------------------------
        # Create
        # -----------------------------------------------------

        corrigendum = TenderCorrigendum(

            tender_id=tender_id,

            corrigendum_no=corrigendum_no,

            title=title,

            document_url=document_url,

            published_date=published_date,

            old_closing_date=old_closing_date,

            new_closing_date=new_closing_date,

            change_summary=change_summary,

            risk_level=risk_level,

            risk_score=risk_score,

            categories=categories,

            detected_changes=detected_changes,

        )

        db.add(corrigendum)

        # NO db.commit()
        # NO db.refresh()

        return corrigendum

    # =========================================================
    # GET BY TENDER
    # =========================================================

    @staticmethod
    def get_by_tender(
        db: Session,
        tender_id: int,
    ):

        return (

            db.query(TenderCorrigendum)

            .filter(
                TenderCorrigendum.tender_id
                == tender_id
            )

            .order_by(
                TenderCorrigendum.created_at.desc()
            )

            .all()

        )

    # =========================================================
    # GET BY DOCUMENT URL
    # =========================================================

    @staticmethod
    def get_by_document_url(
        db: Session,
        tender_id: int,
        document_url: str,
    ):
        """
        Find an existing corrigendum using its
        document URL.

        This is the most reliable duplicate check
        because the same corrigendum may simply be
        displayed as 'Corrigendum' by the website.
        """

        if not document_url:
            return None

        return (

            db.query(TenderCorrigendum)

            .filter(

                TenderCorrigendum.tender_id
                == tender_id,

                TenderCorrigendum.document_url
                == document_url,

            )

            .first()

        )

    # =========================================================
    # GET LATEST CORRIGENDUM
    # =========================================================

    @staticmethod
    def get_latest_by_tender(
        db: Session,
        tender_id: int,
    ):

        return (

            db.query(TenderCorrigendum)

            .filter(
                TenderCorrigendum.tender_id
                == tender_id
            )

            .order_by(
                TenderCorrigendum.created_at.desc()
            )

            .first()

        )

    # =========================================================
    # GENERATE CORRIGENDUM NUMBER
    # =========================================================

    @staticmethod
    def generate_corrigendum_no(
        db: Session,
        tender_id: int,
        corrigendum_text: str | None = None,
        document_url: str | None = None,
    ):
        """
        Generate a stable corrigendum number.

        Examples:

            Corrigendum
            Corrigendum-1
            Corrigendum-2

        If the website already provides a number,
        use that number.

        Otherwise generate the next number based
        on existing corrigendum records.
        """

        import re

        text = (
            corrigendum_text
            or ""
        ).strip()

        url = (
            document_url
            or ""
        ).strip()

        # -----------------------------------------------------
        # Try text
        # -----------------------------------------------------

        match = re.search(
            r"corrigendum"
            r"\s*(?:no\.?|number)?"
            r"\s*[-:#]?\s*(\d+)",
            text,
            re.IGNORECASE,
        )

        if match:

            number = match.group(1)

            return (
                f"Corrigendum-{number}"
            )

        # -----------------------------------------------------
        # Try URL
        # -----------------------------------------------------

        match = re.search(
            r"corrigendum"
            r"[-_\s]*(?:no[-_ ]?)?"
            r"(\d+)",
            url,
            re.IGNORECASE,
        )

        if match:

            number = match.group(1)

            return (
                f"Corrigendum-{number}"
            )

        # -----------------------------------------------------
        # Count existing records
        # -----------------------------------------------------

        existing_count = (

            db.query(
                TenderCorrigendum
            )

            .filter(
                TenderCorrigendum.tender_id
                == tender_id
            )

            .count()

        )

        next_number = (
            existing_count + 1
        )

        return (
            f"Corrigendum-{next_number}"
        )

    # =========================================================
    # RECENT CORRIGENDUMS
    # =========================================================

    @staticmethod
    def get_recent(
        db: Session,
        limit: int = 10,
    ):

        return (

            db.query(TenderCorrigendum)

            .order_by(
                TenderCorrigendum.created_at.desc()
            )

            .limit(limit)

            .all()

        )

    # =========================================================
    # COUNT
    # =========================================================

    @staticmethod
    def get_count(
        db: Session,
        tender_id: int,
    ):

        return (

            db.query(
                TenderCorrigendum
            )

            .filter(
                TenderCorrigendum.tender_id
                == tender_id
            )

            .count()

        )
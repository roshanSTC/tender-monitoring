from sqlalchemy.orm import Session

from models.tender import Tender


class TenderRepository:

    @staticmethod
    def get_existing_tenders(db: Session):

        tenders = db.query(Tender).all()

        existing = {}

        for tender in tenders:

            unique_key = (
                f"{tender.source}|{tender.tender_number}"
            )

            existing[unique_key] = tender

        return existing
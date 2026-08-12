from models.tender import Tender
from services.corrigendum_service import CorrigendumService


class TenderDashboardService:

    @staticmethod
    def get_dashboard(db):

        total_tenders = db.query(Tender).count()

        active_tenders = (
            db.query(Tender)
            .filter(Tender.closing_date != None)
            .count()
        )

        recent_corrigendums = (
            CorrigendumService.get_dashboard_corrigendums(
                db,
                limit=10,
            )
        )

        corrigendum_data = []

        for c in recent_corrigendums:

            corrigendum_data.append({

                "id": c.id,

                "tender_id": c.tender.id,

                "tender_number": c.tender.tender_number,

                "title": c.tender.title,

                "risk_level": c.risk_level,

                "risk_score": c.risk_score,

                "summary": (
                    c.change_summary.split("\n")
                    if c.change_summary
                    else []
                ),

                "published_date": (
                    c.published_date.isoformat()
                    if c.published_date
                    else None
                ),

            })

        return {

            "summary": {

                "total_tenders": total_tenders,

                "active_tenders": active_tenders,

            },

            "recent_corrigendums": corrigendum_data,

        }
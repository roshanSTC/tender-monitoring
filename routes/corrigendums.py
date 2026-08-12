from flask import Blueprint, jsonify

from database.connection import SessionLocal
from services.corrigendum_service import CorrigendumService
from models.tender_corrigendum import TenderCorrigendum

corrigendum_bp = Blueprint(
    "corrigendums",
    __name__,
    url_prefix="/api/corrigendums",
)


@corrigendum_bp.route(
    "/tender/<int:tender_id>",
    methods=["GET"],
)
def get_tender_corrigendums(tender_id):

    db = SessionLocal()

    try:

        corrigendums = (
            CorrigendumService.get_by_tender(
                db,
                tender_id,
            )
        )

        history = []

        for c in corrigendums:

            history.append({

                "id": c.id,

                "corrigendum_no": c.corrigendum_no,

                "title": c.title,

                "document_url": c.document_url,

                "published_date": (
                    c.published_date.isoformat()
                    if c.published_date
                    else None
                ),

                "old_closing_date": (
                    c.old_closing_date.isoformat()
                    if c.old_closing_date
                    else None
                ),

                "new_closing_date": (
                    c.new_closing_date.isoformat()
                    if c.new_closing_date
                    else None
                ),

                "risk_level": c.risk_level,

                "risk_score": c.risk_score,

                "categories": c.categories or [],

                "summary": (
                    c.change_summary.split("\n")
                    if c.change_summary
                    else []
                ),

                "changes": c.detected_changes or []

            })

        return jsonify({

            "success": True,

            "count": len(history),

            "history": history,

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500

    finally:

        db.close()
        

@corrigendum_bp.route(
    "/recent",
    methods=["GET"],
)
def recent_corrigendums():

    db = SessionLocal()

    try:

        corrigendums = (
            CorrigendumService.get_recent(
                db
            )
        )

        return jsonify({

            "success": True,

            "corrigendums": [

                {

                    "id": c.id,

                    "tender_id": c.tender_id,

                    "corrigendum_no": c.corrigendum_no,

                    "title": c.title,

                    "document_url": c.document_url,

                    "published_date": (
                        c.published_date.isoformat()
                        if c.published_date
                        else None
                    ),

                }

                for c in corrigendums

            ],

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e),

        }), 500

    finally:

        db.close()
        
        
@corrigendum_bp.route(
    "/<int:corrigendum_id>",
    methods=["GET"],
)
def corrigendum_details(corrigendum_id):

    db = SessionLocal()

    try:

        corrigendum = CorrigendumService.get_by_id( db, corrigendum_id,)

        if not corrigendum:

            return jsonify({

                "success": False,

                "message": "Corrigendum not found.",

            }), 404

        return jsonify({

            "success": True,

            "corrigendum": {

                "id": corrigendum.id,

                "tender_id": corrigendum.tender_id,

                "corrigendum_no": corrigendum.corrigendum_no,

                "title": corrigendum.title,

                "document_url": corrigendum.document_url,

                "published_date": (
                    corrigendum.published_date.isoformat()
                    if corrigendum.published_date
                    else None
                ),

                "old_closing_date": (
                    corrigendum.old_closing_date.isoformat()
                    if corrigendum.old_closing_date
                    else None
                ),

                "new_closing_date": (
                    corrigendum.new_closing_date.isoformat()
                    if corrigendum.new_closing_date
                    else None
                ),

                "change_summary": corrigendum.change_summary,

            },

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e),

        }), 500

    finally:

        db.close()
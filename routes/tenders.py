from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from database.connection import SessionLocal
from models.tender import Tender
from services.corrigendum_service import CorrigendumService


tenders_bp = Blueprint(
    "tenders",
    __name__,
    url_prefix="/api/tenders"
)

# ============================================================
# SORTING HELPERS
# ============================================================

ALLOWED_SORT_FIELDS = {
    "created_at": "created_at",
    "updated_at": "updated_at",
    "title": "title",
    "source": "source",
    "unit_name": "unit_name",
    "tender_number": "tender_number",
    "publishing_date": "publishing_date",
    "closing_date": "closing_date",
}


def parse_tender_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
    ]

    for date_format in formats:

        try:
            return datetime.strptime(
                value,
                date_format
            )

        except ValueError:
            continue

    return None


def sort_tenders(tenders, sort_by, sort_order):

    reverse = sort_order == "desc"

    if sort_by in [
        "publishing_date",
        "closing_date"
    ]:

        def date_key(tender):

            value = getattr(
                tender,
                sort_by,
                None
            )

            parsed = parse_tender_date(value)

            # Invalid/missing dates go to the end
            if parsed is None:
                return datetime.max

            return parsed

    else:

        def date_key(tender):

            value = getattr(
                tender,
                sort_by,
                None
            )

            if value is None:
                return ""

            return str(value).lower()

    return sorted(
        tenders,
        key=date_key,
        reverse=reverse
    )


@tenders_bp.route("", methods=["GET"])
@jwt_required()
def get_tenders():

    db = SessionLocal()

    try:

        # ---------------------------------------------
        # Query parameters
        # ---------------------------------------------

        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            default=20,
            type=int
        )

        # Keep pagination within reasonable limits
        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        # ---------------------------------------------
        # Optional filters
        # ---------------------------------------------

        source = request.args.get("source")
        unit_name = request.args.get("unit_name")

        query = db.query(Tender)

        if source:
            query = query.filter(
                Tender.source.ilike(f"%{source.strip()}%")
            )

        if unit_name:
            query = query.filter(
                Tender.unit_name.ilike(
                    f"%{unit_name.strip()}%"
                )
            )

        # ---------------------------------------------------
        # Sorting
        # ---------------------------------------------------

        sort_by = (
            request.args.get(
                "sort_by",
                "created_at"
            )
            .strip()
            .lower()
        )

        sort_order = (
            request.args.get(
                "sort_order",
                "desc"
            )
            .strip()
            .lower()
        )

        if sort_by not in ALLOWED_SORT_FIELDS:

            return jsonify({
                "success": False,
                "message": (
                    "Invalid sort_by. Allowed values: "
                    + ", ".join(ALLOWED_SORT_FIELDS.keys())
                )
            }), 400

        if sort_order not in ["asc", "desc"]:

            return jsonify({
                "success": False,
                "message": (
                    "Invalid sort_order. "
                    "Allowed values: asc, desc."
                )
            }), 400


        # ---------------------------------------------------
        # Fetch + sort
        # ---------------------------------------------------

        all_tenders = query.all()

        all_tenders = sort_tenders(
            all_tenders,
            sort_by,
            sort_order
        )

        total = len(all_tenders)

        # ---------------------------------------------------
        # Pagination after sorting
        # ---------------------------------------------------

        offset = (page - 1) * per_page

        tenders = all_tenders[
            offset: offset + per_page
        ]

        # ---------------------------------------------
        # Response
        # ---------------------------------------------

        data = []

        for tender in tenders:

            data.append({
                "id": tender.id,
                "tender_number": tender.tender_number,
                "title": tender.title,
                "source": tender.source,
                "unit_name": tender.unit_name,
                "publishing_date": tender.publishing_date,
                "closing_date": tender.closing_date,
                "tender": tender.tender,
                "tender_url": tender.tender_url,
                "corrigendum": tender.corrigendum,
                "corrigendum_url": tender.corrigendum_url,
                "created_at": (
                    tender.created_at.isoformat()
                    if tender.created_at
                    else None
                ),
                "updated_at": (
                    tender.updated_at.isoformat()
                    if tender.updated_at
                    else None
                )
            })

        return jsonify({
            "success": True,
            "page": page,
            "per_page": per_page,
            "total": total,
            "count": len(data),
            "tenders": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch tenders.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        

@tenders_bp.route("/search", methods=["GET"])
@jwt_required()
def search_tenders():

    db = SessionLocal()

    try:

        search = (
            request.args.get("q") or ""
        ).strip()

        if not search:

            return jsonify({
                "success": False,
                "message": "Search query 'q' is required."
            }), 400

        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            default=20,
            type=int
        )

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        search_pattern = f"%{search}%"

        query = (
            db.query(Tender)
            .filter(
                Tender.title.ilike(search_pattern)
                | Tender.tender_number.ilike(search_pattern)
                | Tender.source.ilike(search_pattern)
                | Tender.unit_name.ilike(search_pattern)
            )
        )

        total = query.count()

        offset = (page - 1) * per_page

        tenders = (
            query
            .order_by(
                Tender.created_at.desc()
            )
            .offset(offset)
            .limit(per_page)
            .all()
        )

        data = []

        for tender in tenders:

            data.append({
                "id": tender.id,
                "tender_number": tender.tender_number,
                "title": tender.title,
                "source": tender.source,
                "unit_name": tender.unit_name,
                "publishing_date": tender.publishing_date,
                "closing_date": tender.closing_date,
                "tender": tender.tender,
                "tender_url": tender.tender_url,
                "corrigendum": tender.corrigendum,
                "corrigendum_url": tender.corrigendum_url,
                "created_at": (
                    tender.created_at.isoformat()
                    if tender.created_at
                    else None
                ),
                "updated_at": (
                    tender.updated_at.isoformat()
                    if tender.updated_at
                    else None
                )
            })

        return jsonify({
            "success": True,
            "query": search,
            "page": page,
            "per_page": per_page,
            "total": total,
            "count": len(data),
            "tenders": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to search tenders.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        
        
@tenders_bp.route("/filter", methods=["GET"])
@jwt_required()
def filter_tenders():

    db = SessionLocal()

    try:

        # ---------------------------------------------
        # Pagination
        # ---------------------------------------------

        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            default=20,
            type=int
        )

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        # ---------------------------------------------
        # Filters
        # ---------------------------------------------

        source = (
            request.args.get("source") or ""
        ).strip()

        unit_name = (
            request.args.get("unit_name") or ""
        ).strip()

        publishing_date_from = (
            request.args.get("publishing_date_from") or ""
        ).strip()

        publishing_date_to = (
            request.args.get("publishing_date_to") or ""
        ).strip()

        closing_date_from = (
            request.args.get("closing_date_from") or ""
        ).strip()

        closing_date_to = (
            request.args.get("closing_date_to") or ""
        ).strip()

        query = db.query(Tender)

        # ---------------------------------------------
        # Source
        # ---------------------------------------------

        if source:

            query = query.filter(
                Tender.source.ilike(
                    f"%{source}%"
                )
            )

        # ---------------------------------------------
        # Unit
        # ---------------------------------------------

        if unit_name:

            query = query.filter(
                Tender.unit_name.ilike(
                    f"%{unit_name}%"
                )
            )

        # ---------------------------------------------
        # Publishing date
        # ---------------------------------------------

        if publishing_date_from:

            try:

                datetime.strptime(
                    publishing_date_from,
                    "%Y-%m-%d"
                )

                query = query.filter(
                    Tender.publishing_date >= (
                        publishing_date_from + " 00:00:00"
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid publishing_date_from. "
                        "Use YYYY-MM-DD."
                    )
                }), 400


        if publishing_date_to:

            try:

                datetime.strptime(
                    publishing_date_to,
                    "%Y-%m-%d"
                )

                query = query.filter(
                    Tender.publishing_date <= (
                        publishing_date_to + " 23:59:59"
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid publishing_date_to. "
                        "Use YYYY-MM-DD."
                    )
                }), 400

        # ---------------------------------------------
        # Closing date
        # ---------------------------------------------

        if closing_date_from:

            try:

                datetime.strptime(
                    closing_date_from,
                    "%Y-%m-%d"
                )

                query = query.filter(
                    Tender.closing_date >= (
                        closing_date_from + " 00:00:00"
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid closing_date_from. "
                        "Use YYYY-MM-DD."
                    )
                }), 400


        if closing_date_to:

            try:

                datetime.strptime(
                    closing_date_to,
                    "%Y-%m-%d"
                )

                query = query.filter(
                    Tender.closing_date <= (
                        closing_date_to + " 23:59:59"
                    )
                )

            except ValueError:

                return jsonify({
                    "success": False,
                    "message": (
                        "Invalid closing_date_to. "
                        "Use YYYY-MM-DD."
                    )
                }), 400

        # ---------------------------------------------
        # Total
        # ---------------------------------------------

        total = query.count()

        # ---------------------------------------------
        # Pagination
        # ---------------------------------------------

        offset = (page - 1) * per_page

        tenders = (
            query
            .order_by(
                Tender.created_at.desc()
            )
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # ---------------------------------------------
        # Response
        # ---------------------------------------------

        data = []

        for tender in tenders:

            data.append({
                "id": tender.id,
                "tender_number": tender.tender_number,
                "title": tender.title,
                "source": tender.source,
                "unit_name": tender.unit_name,
                "publishing_date": tender.publishing_date,
                "closing_date": tender.closing_date,
                "tender": tender.tender,
                "tender_url": tender.tender_url,
                "corrigendum": tender.corrigendum,
                "corrigendum_url": tender.corrigendum_url,
                "created_at": (
                    tender.created_at.isoformat()
                    if tender.created_at
                    else None
                ),
                "updated_at": (
                    tender.updated_at.isoformat()
                    if tender.updated_at
                    else None
                )
            })

        return jsonify({
            "success": True,
            "filters": {
                "source": source or None,
                "unit_name": unit_name or None,
                "publishing_date_from": (
                    publishing_date_from or None
                ),
                "publishing_date_to": (
                    publishing_date_to or None
                ),
                "closing_date_from": (
                    closing_date_from or None
                ),
                "closing_date_to": (
                    closing_date_to or None
                )
            },
            "page": page,
            "per_page": per_page,
            "total": total,
            "count": len(data),
            "tenders": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to filter tenders.",
            "error": str(e)
        }), 500

    finally:

        db.close()



@tenders_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_tenders():

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------

        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 20))
        except ValueError:

            return jsonify({
                "success": False,
                "message": "page and per_page must be integers."
            }), 400

        if page < 1:
            page = 1

        if per_page < 1:
            per_page = 20

        if per_page > 100:
            per_page = 100

        offset = (page - 1) * per_page

        # --------------------------------------------------
        # Current time
        # --------------------------------------------------

        now = datetime.now()

        # --------------------------------------------------
        # Convert closing_date string safely
        #
        # Your existing values are expected to look like:
        #
        # 2025-06-13 15:00:00
        #
        # Invalid values are ignored instead of crashing
        # the entire API.
        # --------------------------------------------------

        closing_date_expr = db.query(
            Tender
        ).filter(
            Tender.closing_date.isnot(None),
            Tender.closing_date != "",
        )

        # --------------------------------------------------
        # Get all candidates first
        # --------------------------------------------------

        candidates = (
            closing_date_expr
            .order_by(Tender.closing_date.asc())
            .all()
        )

        active_tenders = []

        for tender in candidates:

            if not tender.closing_date:
                continue

            closing_date = None

            # Try supported formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d-%m-%Y %H:%M:%S",
                "%d-%m-%Y %H:%M",
                "%d-%m-%Y",
            ]

            for date_format in formats:

                try:
                    closing_date = datetime.strptime(
                        tender.closing_date.strip(),
                        date_format
                    )
                    break

                except ValueError:
                    continue

            # Invalid date -> skip
            if closing_date is None:
                continue

            # Active means closing date has not passed
            if closing_date >= now:
                active_tenders.append(tender)

        # --------------------------------------------------
        # Total
        # --------------------------------------------------

        total = len(active_tenders)

        # --------------------------------------------------
        # Pagination
        # --------------------------------------------------

        paginated_tenders = active_tenders[
            offset: offset + per_page
        ]

        # --------------------------------------------------
        # Response
        # --------------------------------------------------

        data = []

        for tender in paginated_tenders:

            data.append({
                "id": tender.id,
                "source": tender.source,
                "tender_number": tender.tender_number,
                "title": tender.title,
                "unit_name": tender.unit_name,
                "publishing_date": tender.publishing_date,
                "closing_date": tender.closing_date,
                "tender": tender.tender,
                "tender_url": tender.tender_url,
                "corrigendum": tender.corrigendum,
                "corrigendum_url": tender.corrigendum_url,
                "created_at": (
                    tender.created_at.isoformat()
                    if tender.created_at
                    else None
                ),
                "updated_at": (
                    tender.updated_at.isoformat()
                    if tender.updated_at
                    else None
                ),
            })

        return jsonify({
            "success": True,
            "count": len(data),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (
                (total + per_page - 1) // per_page
                if total > 0
                else 0
            ),
            "tenders": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch active tenders.",
            "error": str(e)
        }), 500

    finally:

        db.close()


        
@tenders_bp.route("/<int:tender_id>", methods=["GET"])
@jwt_required()
def get_tender(tender_id):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # Get Tender
        # -------------------------------------------------

        tender = (
            db.query(Tender)
            .filter(
                Tender.id == tender_id
            )
            .first()
        )

        # -------------------------------------------------
        # Tender Not Found
        # -------------------------------------------------

        if not tender:

            return jsonify({
                "success": False,
                "message": "Tender not found."
            }), 404

        # -------------------------------------------------
        # Corrigendum Intelligence
        # -------------------------------------------------

        corrigendum_count = (
            CorrigendumService.get_count(
                db,
                tender.id,
            )
        )

        latest_corrigendum = (
            CorrigendumService.get_latest_by_tender(
                db,
                tender.id,
            )
        )

        # -------------------------------------------------
        # Tender Data
        # -------------------------------------------------

        data = {

            "id": tender.id,

            "tender_number": tender.tender_number,

            "title": tender.title,

            "source": tender.source,

            "unit_name": tender.unit_name,

            "publishing_date": (
                tender.publishing_date.isoformat()
                if tender.publishing_date
                else None
            ),

            "closing_date": (
                tender.closing_date.isoformat()
                if tender.closing_date
                else None
            ),

            "tender": tender.tender,

            "tender_url": tender.tender_url,

            "corrigendum": tender.corrigendum,

            "corrigendum_url": tender.corrigendum_url,

            "created_at": (
                tender.created_at.isoformat()
                if tender.created_at
                else None
            ),

            "updated_at": (
                tender.updated_at.isoformat()
                if tender.updated_at
                else None
            ),

            # -------------------------------------------------
            # Corrigendum Intelligence
            # -------------------------------------------------

            "corrigendum_count": corrigendum_count,

            "latest_corrigendum": (

                {

                    "id": latest_corrigendum.id,

                    "corrigendum_no": (
                        latest_corrigendum.corrigendum_no
                    ),

                    "title": (
                        latest_corrigendum.title
                    ),

                    "document_url": (
                        latest_corrigendum.document_url
                    ),

                    "published_date": (

                        latest_corrigendum.published_date.isoformat()

                        if latest_corrigendum.published_date

                        else None
                    ),

                    "old_closing_date": (

                        latest_corrigendum.old_closing_date.isoformat()

                        if latest_corrigendum.old_closing_date

                        else None
                    ),

                    "new_closing_date": (

                        latest_corrigendum.new_closing_date.isoformat()

                        if latest_corrigendum.new_closing_date

                        else None
                    ),

                    "risk_level": (
                        latest_corrigendum.risk_level
                    ),

                    "risk_score": (
                        latest_corrigendum.risk_score
                    ),

                    "summary": (

                        latest_corrigendum
                        .change_summary
                        .split("\n")

                        if latest_corrigendum.change_summary

                        else []
                    ),

                    "categories": (
                        latest_corrigendum.categories
                    ),

                }

                if latest_corrigendum

                else None

            ),

        }

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "tender": data

        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({

            "success": False,

            "message": "Failed to fetch tender.",

            "error": str(e)

        }), 500

    finally:

        db.close()
        


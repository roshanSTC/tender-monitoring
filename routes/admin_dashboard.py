from flask import Blueprint, jsonify

from database.connection import SessionLocal
from services.admin_dashboard_service import AdminDashboardService

admin_dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/api/admin/dashboard",
)


@admin_dashboard_bp.route("", methods=["GET"])
def get_dashboard():

    db = SessionLocal()

    try:

        result = AdminDashboardService.get_dashboard(db)

        return jsonify({
            "success": True,
            "summary": result["summary"],
            "recent_invitations": result["recent_invitations"],
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

    finally:

        db.close()
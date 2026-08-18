from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, distinct

from database.connection import SessionLocal
from models.tender import Tender
from models.notification import Notification
from models.notification_tender import NotificationTender


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.route("", methods=["GET"])
@jwt_required()
def get_dashboard():

    db = SessionLocal()

    try:

        # =====================================================
        # CURRENT USER
        # =====================================================

        user_id = int(get_jwt_identity())

        now = datetime.now()

        today_start = datetime(
            now.year,
            now.month,
            now.day
        )

        tomorrow_start = today_start + timedelta(days=1)

        # Monday = start of current week
        week_start = today_start - timedelta(
            days=today_start.weekday()
        )

        # =====================================================
        # 1. TOTAL TENDERS
        # =====================================================

        total_tenders = (
            db.query(func.count(Tender.id))
            .scalar()
            or 0
        )

        # =====================================================
        # 2. ACTIVE TENDERS
        # =====================================================

        active_tenders = (
            db.query(func.count(Tender.id))
            .filter(
                Tender.closing_date.isnot(None),
                Tender.closing_date >= now
            )
            .scalar()
            or 0
        )

        # =====================================================
        # 3. TENDERS CREATED TODAY
        # =====================================================

        tenders_today = (
            db.query(func.count(Tender.id))
            .filter(
                Tender.created_at >= today_start,
                Tender.created_at < tomorrow_start
            )
            .scalar()
            or 0
        )

        # =====================================================
        # 4. TENDERS CREATED THIS WEEK
        # =====================================================

        tenders_this_week = (
            db.query(func.count(Tender.id))
            .filter(
                Tender.created_at >= week_start,
                Tender.created_at < tomorrow_start
            )
            .scalar()
            or 0
        )

        # =====================================================
        # 5. UNREAD NOTIFICATIONS
        # CURRENT USER ONLY
        # =====================================================

        unread_notifications = (
            db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False)
            )
            .scalar()
            or 0
        )

        # =====================================================
        # 6. MATCHED TENDERS
        #
        # Distinct tenders linked to this user's notifications
        # =====================================================

        matched_tenders = (
            db.query(
                func.count(
                    distinct(NotificationTender.tender_id)
                )
            )
            .join(
                Notification,
                Notification.id
                == NotificationTender.notification_id
            )
            .filter(
                Notification.user_id == user_id
            )
            .scalar()
            or 0
        )

        # =====================================================
        # 7. TENDERS BY SOURCE
        # FOR GRAPH
        # =====================================================

        source_rows = (
            db.query(
                Tender.source,
                func.count(Tender.id).label("count")
            )
            .filter(
                Tender.source.isnot(None),
                Tender.source != ""
            )
            .group_by(
                Tender.source
            )
            .order_by(
                func.count(Tender.id).desc()
            )
            .all()
        )

        tenders_by_source = []

        for source, count in source_rows:

            tenders_by_source.append({
                "source": source,
                "count": count
            })

        # =====================================================
        # 8. TENDER ACTIVITY
        # LAST 7 DAYS
        # FOR LINE GRAPH
        # =====================================================

        tender_activity = []

        for i in range(6, -1, -1):

            activity_date = (
                today_start
                - timedelta(days=i)
            )

            next_date = (
                activity_date
                + timedelta(days=1)
            )

            count = (
                db.query(func.count(Tender.id))
                .filter(
                    Tender.publishing_date >= activity_date,
                    Tender.publishing_date < next_date
                )
                .scalar()
                or 0
            )

            tender_activity.append({
                "date": activity_date.strftime(
                    "%Y-%m-%d"
                ),
                "count": count
            })

        # =====================================================
        # 9. RECENT TENDERS
        # =====================================================

        recent_tenders = (
            db.query(Tender)
            .order_by(
                Tender.created_at.desc()
            )
            .limit(10)
            .all()
        )

        recent_tenders_data = []

        for tender in recent_tenders:

            recent_tenders_data.append({
                "id": tender.id,
                "tender_number": tender.tender_number,
                "title": tender.title,
                "source": tender.source,
                "unit_name": tender.unit_name,
                "publishing_date": tender.publishing_date,
                "closing_date": tender.closing_date,
                "tender_url": tender.tender_url,
                "corrigendum": tender.corrigendum,
                "corrigendum_url": tender.corrigendum_url,
                "created_at": (
                    tender.created_at.isoformat()
                    if tender.created_at
                    else None
                )
            })

        # =====================================================
        # 10. RECENT NOTIFICATIONS
        # CURRENT USER ONLY
        # =====================================================

        recent_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .limit(10)
            .all()
        )

        recent_notifications_data = []

        for notification in recent_notifications:

            recent_notifications_data.append({
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                ),
                "read_at": (
                    notification.read_at.isoformat()
                    if notification.read_at
                    else None
                )
            })

        # =====================================================
        # RESPONSE
        # =====================================================

        return jsonify({

            "success": True,

            "summary": {

                "total_tenders": total_tenders,

                "active_tenders": active_tenders,

                "tenders_today": tenders_today,

                "tenders_this_week": tenders_this_week,

                "unread_notifications":
                    unread_notifications,

                "matched_tenders":
                    matched_tenders
            },

            "tenders_by_source":
                tenders_by_source,

            "tender_activity":
                tender_activity,

            "recent_tenders":
                recent_tenders_data,

            "recent_notifications":
                recent_notifications_data

        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({

            "success": False,

            "message":
                "Failed to fetch dashboard data.",

            "error": str(e)

        }), 500

    finally:

        db.close()
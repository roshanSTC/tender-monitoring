from datetime import datetime, timezone 

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.connection import SessionLocal
from models.user import User
from models.notification import Notification
from models.notification_tender import NotificationTender
from models.tender import Tender


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notifications"
)


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id
            )
            .order_by(
                Notification.created_at.desc()
            )
            .all()
        )

        data = []

        for notification in notifications:

            data.append({
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "reference_type": notification.reference_type,
                "reference_id": notification.reference_id,
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

        return jsonify({
            "success": True,
            "count": len(data),
            "notifications": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch notifications.",
            "error": str(e)
        }), 500

    finally:

        db.close()   
        
        
@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def get_unread_count():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        unread_count = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False)
            )
            .count()
        )

        return jsonify({
            "success": True,
            "unread_count": unread_count
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch unread notification count.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        

@notifications_bp.route(
    "/<int:notification_id>/read",
    methods=["PATCH"]
)
@jwt_required()
def mark_notification_as_read(notification_id):

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
            .first()
        )

        if not notification:

            return jsonify({
                "success": False,
                "message": "Notification not found."
            }), 404

        if not notification.is_read:

            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            db.commit()

        return jsonify({
            "success": True,
            "message": "Notification marked as read.",
            "notification_id": notification.id
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to mark notification as read.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        

@notifications_bp.route(
    "/read-all",
    methods=["PATCH"]
)
@jwt_required()
def mark_all_notifications_as_read():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        updated_count = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False)
            )
            .update(
                {
                    Notification.is_read: True,
                    Notification.read_at: datetime.now(timezone.utc)
                },
                synchronize_session=False
            )
        )

        db.commit()

        return jsonify({
            "success": True,
            "message": "All notifications marked as read.",
            "updated_count": updated_count
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to mark notifications as read.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        
        
@notifications_bp.route(
    "/<int:notification_id>/tenders",
    methods=["GET"]
)
@jwt_required()
def get_notification_tenders(notification_id):

    db = SessionLocal()

    try:

        # --------------------------------------------
        # Get logged-in user from JWT
        # --------------------------------------------

        user_id = int(get_jwt_identity())

        # --------------------------------------------
        # Verify notification belongs to this user
        # --------------------------------------------

        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
            .first()
        )

        if not notification:

            return jsonify({
                "success": False,
                "message": "Notification not found."
            }), 404

        # --------------------------------------------
        # Get all tenders linked to notification
        # --------------------------------------------

        tender_rows = (
            db.query(Tender)
            .join(
                NotificationTender,
                NotificationTender.tender_id == Tender.id
            )
            .filter(
                NotificationTender.notification_id == notification_id
            )
            .order_by(
                Tender.id.asc()
            )
            .all()
        )

        # --------------------------------------------
        # Format response
        # --------------------------------------------

        tenders = []

        for tender in tender_rows:

            tenders.append({
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
                )
            })

        return jsonify({
            "success": True,
            "notification_id": notification_id,
            "notification_title": notification.title,
            "notification_type": notification.type,
            "tender_count": len(tenders),
            "tenders": tenders
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch notification tenders.",
            "error": str(e)
        }), 500

    finally:

        db.close()
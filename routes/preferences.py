from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.connection import SessionLocal
from models.user_tender_preference import UserTenderPreference


preferences_bp = Blueprint(
    "preferences",
    __name__,
    url_prefix="/api/preferences"
)


# ============================================================
# GET ALL USER PREFERENCES
# ============================================================

@preferences_bp.route("", methods=["GET"])
@jwt_required()
def get_preferences():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        preferences = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.user_id == user_id
            )
            .order_by(
                UserTenderPreference.created_at.desc()
            )
            .all()
        )

        data = []

        for preference in preferences:

            data.append({
                "id": preference.id,
                "preference_type": preference.preference_type,
                "preference_value": preference.preference_value,
                "is_active": preference.is_active,
                "created_at": (
                    preference.created_at.isoformat()
                    if preference.created_at
                    else None
                )
            })

        return jsonify({
            "success": True,
            "count": len(data),
            "preferences": data
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch preferences.",
            "error": str(e)
        }), 500

    finally:

        db.close()


# ============================================================
# CREATE PREFERENCE
# ============================================================

@preferences_bp.route("", methods=["POST"])
@jwt_required()
def create_preference():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        preference_type = (
            data.get("preference_type") or ""
        ).strip().lower()

        preference_value = (
            data.get("preference_value") or ""
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not preference_type:

            return jsonify({
                "success": False,
                "message": "preference_type is required."
            }), 400

        if not preference_value:

            return jsonify({
                "success": False,
                "message": "preference_value is required."
            }), 400

        allowed_types = [
            "keyword",
            "website",
        ]

        if preference_type not in allowed_types:

            return jsonify({
                "success": False,
                "message": (
                    "Invalid preference_type. "
                    "Allowed values: keyword, website."
                )
            }), 400

        # ----------------------------------------------------
        # Prevent duplicate active preference
        # ----------------------------------------------------

        existing = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.user_id == user_id,
                UserTenderPreference.preference_type == preference_type,
                UserTenderPreference.preference_value.ilike(
                    preference_value
                )
            )
            .first()
        )

        if existing:

            return jsonify({
                "success": False,
                "message": "This preference already exists.",
                "preference_id": existing.id,
                "is_active": existing.is_active
            }), 409

        # ----------------------------------------------------
        # Create
        # ----------------------------------------------------

        preference = UserTenderPreference(
            user_id=user_id,
            preference_type=preference_type,
            preference_value=preference_value,
            is_active=True,
        )

        db.add(preference)

        db.commit()

        db.refresh(preference)

        return jsonify({
            "success": True,
            "message": "Preference created successfully.",
            "preference": {
                "id": preference.id,
                "preference_type": preference.preference_type,
                "preference_value": preference.preference_value,
                "is_active": preference.is_active,
                "created_at": (
                    preference.created_at.isoformat()
                    if preference.created_at
                    else None
                )
            }
        }), 201

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to create preference.",
            "error": str(e)
        }), 500

    finally:

        db.close()


# ============================================================
# UPDATE PREFERENCE
# ============================================================

@preferences_bp.route(
    "/<int:preference_id>",
    methods=["PUT"]
)
@jwt_required()
def update_preference(preference_id):

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        preference = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.id == preference_id,
                UserTenderPreference.user_id == user_id
            )
            .first()
        )

        if not preference:

            return jsonify({
                "success": False,
                "message": "Preference not found."
            }), 404

        data = request.get_json() or {}

        preference_value = (
            data.get("preference_value") or ""
        ).strip()

        if not preference_value:

            return jsonify({
                "success": False,
                "message": "preference_value is required."
            }), 400

        # ----------------------------------------------------
        # Check duplicate
        # ----------------------------------------------------

        existing = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.user_id == user_id,
                UserTenderPreference.preference_type
                == preference.preference_type,
                UserTenderPreference.preference_value.ilike(
                    preference_value
                ),
                UserTenderPreference.id != preference_id
            )
            .first()
        )

        if existing:

            return jsonify({
                "success": False,
                "message": "This preference already exists."
            }), 409

        preference.preference_value = preference_value

        db.commit()

        db.refresh(preference)

        return jsonify({
            "success": True,
            "message": "Preference updated successfully.",
            "preference": {
                "id": preference.id,
                "preference_type": preference.preference_type,
                "preference_value": preference.preference_value,
                "is_active": preference.is_active,
                "created_at": (
                    preference.created_at.isoformat()
                    if preference.created_at
                    else None
                )
            }
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to update preference.",
            "error": str(e)
        }), 500

    finally:

        db.close()


# ============================================================
# ENABLE / DISABLE PREFERENCE
# ============================================================

@preferences_bp.route(
    "/<int:preference_id>/toggle",
    methods=["PATCH"]
)
@jwt_required()
def toggle_preference(preference_id):

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        preference = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.id == preference_id,
                UserTenderPreference.user_id == user_id
            )
            .first()
        )

        if not preference:

            return jsonify({
                "success": False,
                "message": "Preference not found."
            }), 404

        preference.is_active = not preference.is_active

        db.commit()

        db.refresh(preference)

        return jsonify({
            "success": True,
            "message": (
                "Preference enabled successfully."
                if preference.is_active
                else "Preference disabled successfully."
            ),
            "preference_id": preference.id,
            "is_active": preference.is_active
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to toggle preference.",
            "error": str(e)
        }), 500

    finally:

        db.close()


# ============================================================
# DELETE PREFERENCE
# ============================================================

@preferences_bp.route(
    "/<int:preference_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_preference(preference_id):

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        preference = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.id == preference_id,
                UserTenderPreference.user_id == user_id
            )
            .first()
        )

        if not preference:

            return jsonify({
                "success": False,
                "message": "Preference not found."
            }), 404

        db.delete(preference)

        db.commit()

        return jsonify({
            "success": True,
            "message": "Preference deleted successfully.",
            "preference_id": preference_id
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to delete preference.",
            "error": str(e)
        }), 500

    finally:

        db.close()
from flask import Blueprint, request, jsonify

from database.connection import SessionLocal
from services.invitation_service import InvitationService
from services.user_service import UserService

admin_users_bp = Blueprint(
    "admin_users",
    __name__,
    url_prefix="/api/admin/users",
)


@admin_users_bp.route("", methods=["GET"])
def get_users():

    db = SessionLocal()

    try:

        users = UserService.get_all_users(db)

        return jsonify({
            "success": True,
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "created_at": (
                        user.created_at.isoformat()
                        if user.created_at
                        else None
                    )
                }
                for user in users
            ]
        })

    except Exception as e:

        return (
            jsonify({
                "success": False,
                "message": str(e)
            }),
            500
        )

    finally:

        db.close()
        

@admin_users_bp.route(
    "/<int:user_id>/status",
    methods=["PATCH"],
)
def update_user_status(user_id):

    db = SessionLocal()

    try:

        data = request.get_json()

        status = data.get("status")
        
        user = UserService.update_status(
            db=db,
            user_id=user_id,
            status=status,
        )

        return jsonify({
            "success": True,
            "message": "User updated successfully.",
            "user": {
                "id": user.id,
                "status": user.status,
            },
        })

    except ValueError as e:

        db.rollback()

        return (
            jsonify({
                "success": False,
                "message": str(e),
            }),
            400,
        )

    except Exception as e:

        db.rollback()

        return (
            jsonify({
                "success": False,
                "message": str(e),
            }),
            500,
        )

    finally:

        db.close()
        

@admin_users_bp.route(
    "/<int:user_id>",
    methods=["DELETE"],
)
def delete_user(user_id):

    db = SessionLocal()

    try:

        UserService.delete_user(
            db,
            user_id,
        )

        return jsonify({
            "success": True,
            "message": "User deleted successfully.",
        })

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

    finally:

        db.close()
        

@admin_users_bp.route(
    "/<int:user_id>/resend",
    methods=["POST"],
)
def resend_user_invitation(user_id):

    db = SessionLocal()

    try:

        user = InvitationService.resend_invitation(
            db,
            user_id,
        )

        return jsonify({
            "success": True,
            "message": "Invitation resent successfully.",
            "user": {
                "id": user.id,
                "email": user.email,
                "status": user.status,
            }
        })

    except ValueError as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": str(e),
        }), 400

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": str(e),
        }), 500

    finally:

        db.close()
        
        

@admin_users_bp.route("/invite", methods=["POST"])
def invite_user():

    db = SessionLocal()

    try:

        data = request.get_json()

        email = data.get("email")
        name = data.get("name")
        role = data.get("role", "USER")

        if not email:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Email is required.",
                    }
                ),
                400,
            )

        if not name:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Name is required.",
                    }
                ),
                400,
            )

        result = InvitationService.invite_user(
            db=db,
            email=email,
            name=name,
            role=role,
        )

        return jsonify(
            {
                "success": True,
                "message": "Invitation created successfully.",
                "user": {
                    "id": result["user"].id,
                    "email": result["user"].email,
                    "name": result["user"].name,
                    "status": result["user"].status,
                    "role": result["user"].role,
                },
            }
        )

    except ValueError as e:

        db.rollback()

        return (
            jsonify(
                {
                    "success": False,
                    "message": str(e),
                }
            ),
            409,
        )

    except Exception as e:

        db.rollback()

        return (
            jsonify(
                {
                    "success": False,
                    "message": str(e),
                }
            ),
            500,
        )

    finally:

        db.close()
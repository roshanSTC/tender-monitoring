from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from database.connection import SessionLocal
from models.user import User
from services.invitation_service import InvitationService
from utils.password import verify_password


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.email == email,
                User.status == "ACTIVE",
            )
            .first()
        )

        if not user:

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        if not user.password_hash:

            return jsonify({
                "success": False,
                "message": "Password is not configured for this user."
            }), 401

        if not verify_password(
            password,
            user.password_hash
        ):

            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401

        access_token = create_access_token(
            identity=str(user.id)
        )

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
            }
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Login failed.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        

@auth_bp.route("/set-password", methods=["POST"])
def set_password():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    token = data.get("token")
    password = data.get("password")

    if not token:

        return jsonify({
            "success": False,
            "message": "Invitation token is required."
        }), 400

    if not password:

        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400

    db = SessionLocal()

    try:

        user = InvitationService.set_password(
            db=db,
            token=token,
            password=password,
        )

        return jsonify({
            "success": True,
            "message": "Password created successfully.",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            }
        }), 200

    except ValueError as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to set password.",
            "error": str(e)
        }), 500

    finally:

        db.close()
        
        
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():

    db = SessionLocal()

    try:

        user_id = int(get_jwt_identity())

        user = (
            db.query(User)
            .filter(
                User.id == user_id,
                # User.is_active.is_(True)
            )
            .first()
        )

        if not user:

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
            }
        }), 200

    except Exception as e:

        db.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to fetch current user.",
            "error": str(e)
        }), 500

    finally:

        db.close()
import hashlib
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from models.user import User
from utils.token import generate_invitation_token
from services.email_service import EmailService
from utils.password import hash_password


class InvitationService:

    @staticmethod
    def invite_user(
        db: Session,
        email: str,
        name: str,
        role: str = "USER",
    ):
        """
        Invite a new user.
        """

        email = email.strip().lower()

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            raise ValueError(
                "User already exists."
            )

        token, token_hash = generate_invitation_token()

        expiry = (
            datetime.utcnow()
            + timedelta(hours=48)
        )

        user = User(
            email=email,
            name=name,
            role=role,
            status="INVITED",
            password_hash=None,
            invitation_token_hash=token_hash,
            invitation_expires_at=expiry,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        email_sent = EmailService.send_invitation_email(
            email=user.email,
            name=user.name,
            token=token,
        )

        if not email_sent:
            raise Exception(
                "Failed to send invitation email."
            )

        return {
            "user": user,
        }

    

    @staticmethod
    def verify_invitation(
        db: Session,
        token_hash: str,
    ):
        """
        Verify invitation token.
        """

        user = (
            db.query(User)
            .filter(
                User.invitation_token_hash
                == token_hash
            )
            .first()
        )

        if not user:
            raise ValueError(
                "Invalid invitation."
            )

        if (
            user.invitation_expires_at
            and user.invitation_expires_at
            < datetime.utcnow()
        ):
            raise ValueError(
                "Invitation has expired."
            )

        if (
            user.invitation_used_at
            is not None
        ):
            raise ValueError(
                "Invitation already used."
            )

        return user

    @staticmethod
    def activate_user(
        db: Session,
        user: User,
        password_hash: str,
    ):
        """
        Activate invited user.
        """

        user.password_hash = password_hash
        user.status = "ACTIVE"

        user.invitation_used_at = (
            datetime.utcnow()
        )

        user.invitation_token_hash = None
        user.invitation_expires_at = None

        db.commit()
        db.refresh(user)

        return user
    
    @staticmethod
    def set_password(
        db,
        token: str,
        password: str,
    ):
        """
        Activate invited account.
        """

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        user = (
            db.query(User)
            .filter(
                User.invitation_token_hash == token_hash
            )
            .first()
        )

        if not user:
            raise ValueError(
                "Invalid invitation token."
            )

        if user.status != "INVITED":
            raise ValueError(
                "Invitation already used."
            )

        if (
            user.invitation_expires_at
            and datetime.utcnow()
            > user.invitation_expires_at
        ):
            raise ValueError(
                "Invitation expired."
            )

        user.password_hash = hash_password(password)

        user.status = "ACTIVE"

        # user.is_active = True

        user.invitation_used_at = datetime.utcnow()

        user.invitation_token_hash = None

        user.invitation_expires_at = None

        db.commit()

        db.refresh(user)

        return user
    
    @staticmethod
    def resend_invitation(db, user_id):

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise ValueError("User not found.")

        if user.status != "INVITED":
            raise ValueError(
                "Only invited users can receive a new invitation."
            )

        token = secrets.token_urlsafe(32)

        user.invitation_token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        user.invitation_expires_at = (
            datetime.utcnow() + timedelta(days=2)
        )

        db.commit()
        db.refresh(user)

        EmailService.send_invitation_email(
            email=user.email,
            name=user.name,
            token=token,
        )

        return user
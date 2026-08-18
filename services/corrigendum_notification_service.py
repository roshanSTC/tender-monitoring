from datetime import datetime
import config

from models.notification import Notification
from models.notification_tender import NotificationTender
from models.user import User
from models.user_preference import UserPreference
from models.user_tender_preference import UserTenderPreference
from config import logger
from services.email_service import EmailService
from services.template_service import TemplateService


class CorrigendumNotificationService:

    # =========================================================
    # MAIN NOTIFICATION METHOD
    # =========================================================

    @staticmethod
    def notify(
        db,
        tender,
        corrigendum,
    ):
        """
        Create in-app notifications and send email notifications
        for users who were previously interested in the tender.

        A user is considered interested if they have previously
        received a notification for this tender.

        Duplicate protection:
        Same user + same corrigendum will only be notified once.
        """

        users = (
            CorrigendumNotificationService
            .get_interested_users(
                db=db,
                tender_id=tender.id,
            )
        )

        if not users:

            logger.info(
                f"No historical recipients found for "
                f"{tender.tender_number}. "
                f"Trying keyword preferences."
            )

            users = (
                CorrigendumNotificationService
                .get_users_matching_preferences(
                    db=db,
                    tender=tender,
                )
            )

        print(
            f"Corrigendum notification recipients: "
            f"{len(users)}"
        )

        results = []

        for user in users:
            
            logger.info(
                f"Recipient -> "
                f"{user.id} | {user.email}"
            )

            result = (
                CorrigendumNotificationService
                .notify_user(
                    db=db,
                    user=user,
                    tender=tender,
                    corrigendum=corrigendum,
                )
            )

            results.append(result)

        return results

    # =========================================================
    # FIND USERS INTERESTED IN TENDER
    # =========================================================

    @staticmethod
    def get_interested_users(
        db,
        tender_id,
    ):
        """
        Find users who have previously received a notification
        related to this tender.

        Supports:

        1. Individual tender notifications
        2. Batch tender notifications through NotificationTender
        """

        # -----------------------------------------------------
        # Users from individual tender notifications
        # -----------------------------------------------------

        individual_user_ids = (
            db.query(Notification.user_id)
            .filter(
                Notification.reference_type == "tender",
                Notification.reference_id == tender_id,
            )
            .distinct()
            .all()
        )

        user_ids = {
            row[0]
            for row in individual_user_ids
        }

        # -----------------------------------------------------
        # Users from batch notifications
        # -----------------------------------------------------

        batch_user_ids = (
            db.query(Notification.user_id)
            .join(
                NotificationTender,
                NotificationTender.notification_id
                == Notification.id,
            )
            .filter(
                NotificationTender.tender_id == tender_id,
            )
            .distinct()
            .all()
        )

        user_ids.update(
            row[0]
            for row in batch_user_ids
        )

        if not user_ids:
            return []

        # -----------------------------------------------------
        # Load users
        # -----------------------------------------------------

        users = (
            db.query(User)
            .filter(
                User.id.in_(user_ids)
            )
            .all()
        )

        return users

    # =========================================================
    # NOTIFY ONE USER
    # =========================================================

    @staticmethod
    def notify_user(
        db,
        user,
        tender,
        corrigendum,
    ):
        """
        Create in-app notification and/or send email
        according to the user's notification preferences.

        Duplicate protection:
        Same user + same corrigendum will only be
        processed once.
        """

        # =====================================================
        # DUPLICATE CHECK
        # =====================================================

        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.type == "corrigendum",
                Notification.reference_type == "corrigendum",
                Notification.reference_id == corrigendum.id,
            )
            .first()
        )

        if existing_notification:

            print(
                f"Skipping duplicate corrigendum notification "
                f"for user={user.id}, "
                f"corrigendum={corrigendum.id}"
            )

            return {
                "user_id": user.id,
                "email": user.email,
                "notification_id": existing_notification.id,
                "notification_created": False,
                "email_sent": existing_notification.email_sent,
                "skipped": True,
            }

        # =====================================================
        # LOAD USER NOTIFICATION PREFERENCES
        # =====================================================

        preference = (
            db.query(UserPreference)
            .filter(
                UserPreference.user_id == user.id
            )
            .first()
        )

        # Default behaviour
        in_app_enabled = True
        email_enabled = True

        if preference:

            in_app_enabled = preference.in_app_enabled
            email_enabled = preference.email_enabled

        print(
            f"User {user.id} notification preferences: "
            f"in_app={in_app_enabled}, "
            f"email={email_enabled}"
        )

        # =====================================================
        # BUILD MESSAGE
        # =====================================================

        title = (
            f"Corrigendum Update - "
            f"{tender.tender_number}"
        )

        message = (
            f"A new corrigendum has been issued for "
            f"tender {tender.tender_number}: "
            f"{tender.title}"
        )

        if corrigendum.change_summary:

            message += (
                "\n\nChanges:\n"
                f"{corrigendum.change_summary}"
            )

        if corrigendum.new_closing_date:

            message += (
                "\n\nNew Closing Date: "
                f"{corrigendum.new_closing_date}"
            )

        # =====================================================
        # IN-APP NOTIFICATION
        # =====================================================

        notification = None

        if in_app_enabled:

            notification = Notification(
                user_id=user.id,
                type="corrigendum",
                title=title,
                message=message,
                reference_type="corrigendum",
                reference_id=corrigendum.id,
                is_read=False,
                email_sent=False,
            )

            db.add(notification)

            # Generate notification ID
            db.flush()

            print(
                f"In-app corrigendum notification created "
                f"for user={user.id}"
            )

        else:

            print(
                f"In-app notification disabled "
                f"for user={user.id}"
            )

        # =====================================================
        # EMAIL
        # =====================================================

        email_sent = False

        if email_enabled and user.email:

            try:

                html_body = TemplateService.render(
                    "emails/corrigendum.html",

                    user_name=user.name or user.email,

                    tender_number=tender.tender_number,

                    tender_title=tender.title,

                    source=tender.source,

                    corrigendum_no=corrigendum.corrigendum_no,

                    published_date=corrigendum.published_date,

                    old_closing_date=corrigendum.old_closing_date,

                    new_closing_date=corrigendum.new_closing_date,

                    change_summary=corrigendum.change_summary,

                    corrigendum_url=corrigendum.document_url,
                )

                print(
                    f"Sending corrigendum email to {user.email}"
                )

                email_sent = EmailService.send_email(
                    to_email=user.email,
                    subject=(
                        f"Corrigendum Update - "
                        f"{tender.tender_number}"
                    ),
                    html=html_body,
                )

                if email_sent:

                    if notification:

                        notification.email_sent = True

                        notification.email_sent_at = (
                            datetime.utcnow()
                        )

                    print(
                        f"Corrigendum email sent "
                        f"to {user.email}"
                    )

                else:

                    print(
                        f"Corrigendum email failed "
                        f"for {user.email}"
                    )

            except Exception as e:

                print(
                    f"Corrigendum email failed "
                    f"for {user.email}: {e}"
                )

        elif not email_enabled:

            print(
                f"Email notification disabled "
                f"for user={user.id}"
            )

        elif not user.email:

            print(
                f"User {user.id} has no email address"
            )

        # =====================================================
        # RESULT
        # =====================================================

        return {
            "user_id": user.id,
            "email": user.email,
            "notification_id": (
                notification.id
                if notification
                else None
            ),
            "notification_created": (
                notification is not None
            ),
            "email_sent": email_sent,
            "skipped": False,
        }

    # =========================================================
    # SEND EMAIL
    # =========================================================

    @staticmethod
    def send_email(
        user,
        tender,
        corrigendum,
    ):
        """
        Send corrigendum email.

        Uses the existing TenderMailer.
        """

        from notifications.mailer import TenderMailer

        mailer = TenderMailer()

        subject = (
            f"Corrigendum Update - "
            f"{tender.tender_number}"
        )
        
        tender_url = (
            f"{config.FRONTEND_URL}"
            f"/tenders/{tender.id}"
        )

        corrigendum_url = (
            corrigendum.document_url
        )

        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">

            <h2>Corrigendum Update</h2>

            <p>
                Hello {user.name or user.email},
            </p>

            <p>
                A new corrigendum has been issued for a tender
                matching your preferences.
            </p>

            <hr>

            <h3>Tender Details</h3>

            <p>
                <strong>Tender Number:</strong>
                {tender.tender_number}
            </p>

            <p>
                <strong>Tender Title:</strong>
                {tender.title}
            </p>

            <p>
                <strong>Source:</strong>
                {tender.source}
            </p>

            <h3>Corrigendum Details</h3>

            <p>
                <strong>Corrigendum No:</strong>
                {corrigendum.corrigendum_no}
            </p>

            <p>
                <strong>Published Date:</strong>
                {corrigendum.published_date or "N/A"}
            </p>

        """

        if corrigendum.old_closing_date:

            email_body += f"""
            <p>
                <strong>Previous Closing Date:</strong>
                {corrigendum.old_closing_date}
            </p>
            """

        if corrigendum.new_closing_date:

            email_body += f"""
            <p>
                <strong>New Closing Date:</strong>
                {corrigendum.new_closing_date}
            </p>
            """

        if corrigendum.change_summary:

            email_body += f"""
            <h3>Changes</h3>

            <p>
                {corrigendum.change_summary.replace(chr(10), "<br>")}
            </p>
            """

        email_body += f"""
        <p>

            <a
                href="{tender_url}"
                style="
                    background:#16a34a;
                    color:white;
                    padding:10px 16px;
                    text-decoration:none;
                    border-radius:5px;
                    margin-right:10px;
                "
            >
                View Tender
            </a>

        """

        if corrigendum_url:

            email_body += f"""
            <a
                href="{corrigendum_url}"
                style="
                    background:#2563eb;
                    color:white;
                    padding:10px 16px;
                    text-decoration:none;
                    border-radius:5px;
                "
            >
                View Corrigendum
            </a>
            """

        email_body += "</p>"

        email_body += """
            <hr>

            <p>
                Please log in to the Tender Monitoring System
                for complete details.
            </p>

            <p>
                Regards,<br>
                Tender Monitoring System
            </p>

        </body>
        </html>
        """

        try:

            result = mailer.send_user_email(
                recipient_email=user.email,
                subject=subject,
                html_body=email_body,
            )
            
            print("MAIL RESULT:", result)

            return bool(result)

        except Exception as e:

            print(
                f"Corrigendum email failed for "
                f"{user.email}: {e}"
            )

            return False
        
        
    @staticmethod
    def get_users_matching_preferences(
        db,
        tender,
    ):
        """
        Find users whose active keyword
        preferences match the tender title.
        """

        title = (
            tender.title or ""
        ).lower()

        matched_user_ids = set()

        preferences = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.preference_type == "keyword",
                UserTenderPreference.is_active == True,
            )
            .all()
        )

        for pref in preferences:

            keyword = (
                pref.preference_value or ""
            ).strip().lower()

            if not keyword:
                continue

            if keyword in title:

                matched_user_ids.add(
                    pref.user_id
                )

                logger.info(
                    f"Keyword matched: "
                    f"{keyword} -> "
                    f"{tender.tender_number}"
                )

        if not matched_user_ids:
            return []

        return (
            db.query(User)
            .filter(
                User.id.in_(matched_user_ids)
            )
            .all()
        )
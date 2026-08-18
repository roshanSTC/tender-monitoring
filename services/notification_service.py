from collections import defaultdict
from datetime import datetime

from database.connection import SessionLocal

from models import (
    Notification,
    NotificationTender,
    UserPreference,
)

from services.matching_service import get_matching_users

from notifications.mailer import TenderMailer
from services.template_service import TemplateService


def create_tender_notifications(tender):
    """
    Create in-app notifications and send emails
    for users matching the supplied tender.

    Duplicate protection:
    Same user + same tender will only be notified once.
    """

    mailer = TenderMailer()

    db = SessionLocal()

    try:

        matched_users = get_matching_users(tender)
        
        print(
            f"Matched users: {len(matched_users)}"
        )
        

        results = []

        for user in matched_users:
            
            print(
                    f"Matched user: "
                    f"id={user.id}, "
                    f"email={user.email}"
                )

            # --------------------------------
            # CHECK DUPLICATE FIRST
            # --------------------------------

            existing = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user.id,
                    Notification.reference_type == "tender",
                    Notification.reference_id == tender["id"],
                )
                .first()
            )

            if existing:

                print(
                    f"Skipping duplicate notification "
                    f"for user {user.email}, "
                    f"tender {tender['id']}"
                )

                results.append({
                    "user_id": user.id,
                    "email": user.email,
                    "notification_created": False,
                    "email_sent": False,
                    "skipped": True,
                })

                continue

            # --------------------------------
            # GET USER PREFERENCES
            # --------------------------------

            preference = (
                db.query(UserPreference)
                .filter(
                    UserPreference.user_id == user.id
                )
                .first()
            )

            in_app_enabled = True
            email_enabled = True

            if preference:

                in_app_enabled = (
                    preference.in_app_enabled
                )

                email_enabled = (
                    preference.email_enabled
                )

            title = (
                "New Tender Matching Your Preferences"
            )

            message = (
                f"A new tender matching your preferences "
                f"has been found: {tender['Tender Title']}"
            )

            # --------------------------------
            # IN-APP NOTIFICATION
            # --------------------------------

            notification_created = False

            if in_app_enabled:

                notification = Notification(
                    user_id=user.id,
                    type="tender",
                    title=title,
                    message=message,
                    reference_type="tender",
                    reference_id=tender["id"],
                    is_read=False,
                    email_sent=False,
                )

                db.add(notification)

                

            email_sent = False

            # ---------------------------------------------------
            # EMAIL
            # ---------------------------------------------------

            if email_enabled and user.email:

                # Find existing notification
                notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user.id,
                        Notification.type == "tender",
                        Notification.reference_type == "tender",
                        Notification.reference_id == tender["id"],
                    )
                    .first()
                )

                # Only send email if it hasn't already been sent
                if notification and notification.email_sent:

                    print(
                        f"Email already sent to {user.email} "
                        f"for tender {tender['id']}"
                    )

                else:

                    subject = title

                    email_body = f"""
            Hello {user.name or user.email},

            A new tender matching your preferences has been found.

            Tender:
            {tender["Tender Title"]}

            Tender Number:
            {tender["Tender Number"]}

            Source:
            {tender["Source"]}

            Please log in to the Tender Monitoring System
            to view the complete tender details.

            Regards,
            Tender Monitoring System
            """

                    try:

                        mailer.send_user_email(
                            recipient_email=user.email,
                            subject=subject,
                            html_body=email_body,
                        )
                        
                        # ONLY after successful send
                        mark_email_sent(
                            notification.id,
                        )


                        email_sent = True

                        if notification:

                            notification.email_sent = True
                            notification.email_sent_at = datetime.utcnow()

                        print(
                            f"User email sent successfully to "
                            f"{user.email}"
                        )

                    except Exception as email_error:

                        print(
                            f"Email failed for {user.email}: "
                            f"{email_error}"
                        )

            # --------------------------------
            # SAVE RESULT
            # --------------------------------

            results.append({
                "user_id": user.id,
                "email": user.email,
                "notification_created":
                    notification_created,
                "email_sent":
                    email_sent,
                "skipped": False,
            })

        db.commit()

        return results

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def mark_email_sent(notification_id):
    
    db = SessionLocal()

    try:

        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id
            )
            .first()
        )

        if not notification:
            raise ValueError(
                f"Notification {notification_id} not found"
            )

        notification.email_sent = True
        notification.email_sent_at = datetime.utcnow()

        db.commit()

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()
        
        
def prepare_batch_notifications(matched_users, new_tenders):
    """
    Prepare one notification batch per user.

    Only tenders that have NOT already been notified
    to that user are included.
    """

    db = SessionLocal()

    try:

        batches = []

        if not matched_users:
            return batches

        for user_id, match_data in matched_users.items():

            user = match_data["user"]

            matched_tenders = match_data["tenders"]

            if not matched_tenders:
                continue

            tender_ids = [
                tender["id"]
                for tender in matched_tenders
                if tender.get("id") is not None
            ]

            if not tender_ids:
                continue

            # --------------------------------------------
            # Find tenders already notified to this user
            # --------------------------------------------

            already_notified = (
                db.query(NotificationTender.tender_id)
                .join(
                    Notification,
                    Notification.id
                    == NotificationTender.notification_id
                )
                .filter(
                    Notification.user_id == user.id,
                    NotificationTender.tender_id.in_(tender_ids),
                )
                .all()
            )

            already_notified_ids = {
                row[0]
                for row in already_notified
            }

            # --------------------------------------------
            # Keep only NEW matching tenders
            # --------------------------------------------

            user_new_tenders = [
                tender
                for tender in matched_tenders
                if tender["id"] not in already_notified_ids
            ]

            if not user_new_tenders:

                print(
                    f"No new tenders to notify for "
                    f"user {user.email}"
                )

                continue

            # --------------------------------------------
            # Create ONE batch for this user
            # --------------------------------------------

            batches.append({
                "user_id": user.id,
                "email": user.email,
                "tenders": user_new_tenders,
            })

        return batches

    finally:

        db.close()
        
        
def create_batch_in_app_notifications(batches):
    """
    Create one in-app notification for each user.

    Each notification represents the complete batch of
    matching tenders for that user.

    Also stores the relationship between the notification
    and every tender included in the batch.
    """

    db = SessionLocal()

    try:

        results = []

        for batch in batches:

            user_id = batch["user_id"]
            tenders = batch["tenders"]

            if not tenders:
                continue

            tender_count = len(tenders)

            title = (
                f"{tender_count} New Tender"
                f"{'s' if tender_count != 1 else ''} "
                f"Matching Your Preferences"
            )

            message_lines = [
                "New tenders matching your preferences:"
            ]

            for tender in tenders:

                message_lines.append(
                    f"- {tender['Tender Title']}"
                )

            message = "\n".join(message_lines)

            # --------------------------------------------
            # CREATE ONE NOTIFICATION
            # --------------------------------------------

            notification = Notification(
                user_id=user_id,
                type="tender_batch",
                title=title,
                message=message,
                reference_type="tender_batch",
                reference_id=None,
                is_read=False,
                email_sent=False,
            )

            db.add(notification)

            # Make sure notification.id is available
            db.flush()

            # --------------------------------------------
            # LINK EACH TENDER TO NOTIFICATION
            # --------------------------------------------

            for tender in tenders:

                notification_tender = NotificationTender(
                    notification_id=notification.id,
                    tender_id=tender["id"],
                )

                db.add(notification_tender)

            results.append({
                "user_id": user_id,
                "notification_id": notification.id,
                "notification_created": True,
                "tender_count": tender_count,
            })

        db.commit()

        return results

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()
        
        
def send_batch_emails(batches, in_app_results):

    db = SessionLocal()
    mailer = TenderMailer()

    results = []

    try:
        
        notification_map = {
            result["user_id"]: result["notification_id"]
            for result in in_app_results
            if result.get("notification_created")
        }

        for batch in batches:

            user_id = batch["user_id"]
            user_email = batch["email"]
            tenders = batch["tenders"]

            if not tenders:
                continue

            subject = (
                f"{len(tenders)} New Tender"
                f"{'s' if len(tenders) != 1 else ''} "
                f"Matching Your Preferences"
            )

            email_lines = [
                "New tenders matching your preferences:",
                ""
            ]

            for tender in tenders:

                email_lines.append(
                    f"Tender Number: {tender['Tender Number']}"
                )

                email_lines.append(
                    f"Title: {tender['Tender Title']}"
                )

                email_lines.append(
                    f"Source: {tender['Source']}"
                )

                if tender.get("Tender URL"):

                    email_lines.append(
                        f"Tender URL: {tender['Tender URL']}"
                    )

                if tender.get("Corrigendum URL"):

                    email_lines.append(
                        f"Corrigendum URL: "
                        f"{tender['Corrigendum URL']}"
                    )

                email_lines.append("")
                email_lines.append("----------------------")
                email_lines.append("")
                
            grouped_tenders = defaultdict(list)

            for tender in tenders:
                source = tender.get("Source", "Other")
                grouped_tenders[source].append(tender)

            email_body = TemplateService.render(
                        "emails/tender_match.html",
                        grouped_tenders=dict(grouped_tenders),
                        tender_count=len(tenders),
                        user_email=user_email,
                    )

            try:

                sent = mailer.send_user_email(
                    recipient_email=user_email,
                    subject=subject,
                    html_body=email_body,
                )

                email_sent = bool(sent)
                
                notification_id = notification_map.get(user_id)
                

                # ----------------------------------------
                # UPDATE NOTIFICATION AFTER EMAIL SUCCESS
                # ----------------------------------------

                if email_sent and notification_id:

                    notification = (
                        db.query(Notification)
                        .filter(
                            Notification.user_id == user_id,
                            Notification.type == "tender_batch",
                            Notification.email_sent == False,
                        )
                        .order_by(
                            Notification.id.desc()
                        )
                        .first()
                    )

                    if notification:

                        notification.email_sent = True

                        notification.email_sent_at = (
                            datetime.utcnow()
                        )

                        db.commit()

                        print(
                            f"Email status updated for "
                            f"user {user_email}"
                        )

                results.append({
                    "user_id": user_id,
                    "email": user_email,
                    "tender_count": len(tenders),
                    "email_sent": email_sent,
                })

            except Exception as e:

                print(
                    f"Email failed for {user_email}: {e}"
                )

                results.append({
                    "user_id": user_id,
                    "email": user_email,
                    "tender_count": len(tenders),
                    "email_sent": False,
                })

        return results

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()
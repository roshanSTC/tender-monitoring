from models.corrigendum_notification import (
    CorrigendumNotification
)


class CorrigendumNotificationLogService:

    @staticmethod
    def create(
        db,
        corrigendum_id,
        user_id,
        notification_id=None,
        email_sent=False,
    ):

        record = CorrigendumNotification(
            corrigendum_id=corrigendum_id,
            user_id=user_id,
            notification_id=notification_id,
            email_sent=email_sent,
        )

        db.add(record)

        return record
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Boolean,
)

from database.base import Base


class CorrigendumNotification(Base):

    __tablename__ = "corrigendum_notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    corrigendum_id = Column(
        Integer,
        ForeignKey(
            "corrigendums.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    notification_id = Column(
        Integer,
        ForeignKey(
            "notifications.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    email_sent = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
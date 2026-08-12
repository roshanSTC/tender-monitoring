from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
)

from database.base import Base


class NotificationTender(Base):

    __tablename__ = "notification_tenders"

    id = Column(
        Integer,
        primary_key=True,
    )

    notification_id = Column(
        Integer,
        ForeignKey("notifications.id"),
        nullable=False,
    )

    tender_id = Column(
        Integer,
        ForeignKey("tenders.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "notification_id",
            "tender_id",
            name="uq_notification_tender",
        ),
    )
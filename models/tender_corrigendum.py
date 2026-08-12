from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.base import Base


class TenderCorrigendum(Base):

    __tablename__ = "corrigendums"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    tender_id: Mapped[int] = mapped_column(
        ForeignKey("tenders.id"),
        nullable=False,
        index=True,
    )

    corrigendum_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    document_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    published_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    old_closing_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    new_closing_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    change_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    risk_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    categories: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    detected_changes: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    tender = relationship(
        "Tender",
        back_populates="corrigendums",
    )
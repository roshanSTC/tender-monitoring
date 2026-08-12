from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.base import Base


class Tender(Base):

    __tablename__ = "tenders"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    source = Column(
        String(255),
        nullable=False,
        index=True,
    )

    tender_number = Column(
        String(255),
        nullable=False,
    )

    title = Column(
        Text,
        nullable=True,
    )

    unit_name = Column(
        String(255),
        nullable=True,
        index=True,
    )

    publishing_date = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    closing_date = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    tender = Column(
        Text,
        nullable=True,
    )

    tender_url = Column(
        Text,
        nullable=True,
    )

    corrigendum = Column(Text, nullable=True)
    corrigendum_url = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    corrigendums = relationship(
        "TenderCorrigendum",
        back_populates="tender",
        cascade="all, delete-orphan",
        order_by="TenderCorrigendum.created_at.desc()",
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "tender_number",
            name="uq_tender_source_number",
        ),
    )
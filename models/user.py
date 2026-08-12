from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class User(Base):

    __tablename__ = "users"
    
    

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    password_hash = Column(
        String(255),
        nullable=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="INVITED",
        nullable=False,
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        default="USER",
        nullable=False,
    )
    
    invitation_token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    invitation_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    invitation_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
        )
    
    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    tender_preferences = relationship(
        "UserTenderPreference",
        back_populates="user",
        cascade="all, delete-orphan",
    )
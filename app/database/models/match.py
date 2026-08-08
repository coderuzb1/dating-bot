from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user1_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user2_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user1 = relationship(
        "User",
        foreign_keys=[user1_id],
        back_populates="matches_as_user1",
    )

    user2 = relationship(
        "User",
        foreign_keys=[user2_id],
        back_populates="matches_as_user2",
    )

    __table_args__ = (
        UniqueConstraint(
            "user1_id",
            "user2_id",
            name="uq_match_users",
        ),
    )

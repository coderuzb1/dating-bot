from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    referrer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    referred_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    referrer = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrals",
    )

    referred_user = relationship(
        "User",
        foreign_keys=[referred_user_id],
        back_populates="referred_by",
    )

    __table_args__ = (
        UniqueConstraint(
            "referrer_id",
            "referred_user_id",
            name="uq_referral_pair",
        ),
    )

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    from_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    to_user_id: Mapped[int] = mapped_column(
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

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id],
        back_populates="sent_likes",
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id],
        back_populates="received_likes",
    )

    __table_args__ = (
        UniqueConstraint(
            "from_user_id",
            "to_user_id",
            name="uq_like_from_to",
        ),
    )

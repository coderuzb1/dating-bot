from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Statistics(Base):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    new_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    active_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_likes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_matches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "date",
            name="uq_statistics_date",
        ),
    )

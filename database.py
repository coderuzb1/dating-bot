from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from sqlalchemy.orm import DeclarativeBase

from config import DATABASE_URL


DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1
)


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
      from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    first_name: Mapped[str] = mapped_column(
        String(100)
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    age: Mapped[int] = mapped_column(
        Integer
    )

    gender: Mapped[str] = mapped_column(
        String(20)
    )

    looking_for: Mapped[str] = mapped_column(
        String(20)
    )

    city: Mapped[str] = mapped_column(
        String(100)
    )

    bio: Mapped[str] = mapped_column(
        Text
    )

    premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    photos = relationship(
        "Photo",
        back_populates="user",
        cascade="all, delete-orphan"
)
class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE")
    )

    file_id: Mapped[str] = mapped_column(
        Text
    )

    photo_order: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    user = relationship(
        "User",
        back_populates="photos"
    )


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    from_user: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE")
    )

    to_user: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE")
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user1: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE")
    )

    user2: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE")
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )
from sqlalchemy import select


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user(telegram_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def add_user(user: User):
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def update_user(user: User):
    async with AsyncSessionLocal() as session:
        await session.merge(user)
        await session.commit()


async def delete_user(telegram_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, telegram_id)
        if user:
            await session.delete(user)
            await session.commit()

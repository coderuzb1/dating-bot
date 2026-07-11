import aiosqlite

DB_NAME = "dating.db"

async def create_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            looking_for TEXT,
            city TEXT,
            photo TEXT,
            bio TEXT,
            premium INTEGER DEFAULT 0
        )
        """)
        await db.commit()

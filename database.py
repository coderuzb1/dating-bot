import aiosqlite
from config import DATABASE_NAME


class Database:

    def __init__(self):
        self.db_name = DATABASE_NAME

    async def connect(self):
        db = await aiosqlite.connect(self.db_name)
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON;")
        return db

    async def create_tables(self):

        db = await self.connect()

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            looking TEXT NOT NULL,
            city TEXT NOT NULL,
            bio TEXT,
            premium INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS photos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            photo_order INTEGER NOT NULL,
            FOREIGN KEY(user_id)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS likes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(from_user,to_user),
            FOREIGN KEY(from_user)
            REFERENCES users(user_id)
            ON DELETE CASCADE,
            FOREIGN KEY(to_user)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS matches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1 INTEGER NOT NULL,
            user2 INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1,user2),
            FOREIGN KEY(user1)
            REFERENCES users(user_id)
            ON DELETE CASCADE,
            FOREIGN KEY(user2)
            REFERENCES users(user_id)
            ON DELETE CASCADE
        );
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await db.commit()
        await db.close()
      async def add_user(
        self,
        user_id,
        username,
        first_name,
        name,
        age,
        gender,
        looking,
        city,
        bio
    ):
        db = await self.connect()

        await db.execute("""
        INSERT OR REPLACE INTO users(
            user_id,
            username,
            first_name,
            name,
            age,
            gender,
            looking,
            city,
            bio
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            username,
            first_name,
            name,
            age,
            gender,
            looking,
            city,
            bio
        ))

        await db.commit()
        await db.close()


    async def get_user(self, user_id):
        db = await self.connect()

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )

        user = await cursor.fetchone()

        await db.close()

        return user


    async def user_exists(self, user_id):
        db = await self.connect()

        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )

        result = await cursor.fetchone()

        await db.close()

        return result is not None


    async def update_user(
        self,
        user_id,
        name,
        age,
        gender,
        looking,
        city,
        bio
    ):
        db = await self.connect()

        await db.execute("""
        UPDATE users
        SET
            name = ?,
            age = ?,
            gender = ?,
            looking = ?,
            city = ?,
            bio = ?
        WHERE user_id = ?
        """, (
            name,
            age,
            gender,
            looking,
            city,
            bio,
            user_id
        ))

        await db.commit()
        await db.close()


    async def delete_user(self, user_id):
        db = await self.connect()

        await db.execute(
            "DELETE FROM users WHERE user_id = ?",
            (user_id,)
        )

        await db.commit()
        await db.close()
      async def add_photo(
        self,
        user_id,
        file_id,
        photo_order
    ):
        db = await self.connect()

        await db.execute("""
        INSERT INTO photos(
            user_id,
            file_id,
            photo_order
        )
        VALUES(?,?,?)
        """, (
            user_id,
            file_id,
            photo_order
        ))

        await db.commit()
        await db.close()


    async def get_photos(self, user_id):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT *
        FROM photos
        WHERE user_id = ?
        ORDER BY photo_order
        """, (user_id,))

        photos = await cursor.fetchall()

        await db.close()

        return photos


    async def get_photo(self, user_id, photo_order):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT *
        FROM photos
        WHERE user_id = ?
        AND photo_order = ?
        """, (
            user_id,
            photo_order
        ))

        photo = await cursor.fetchone()

        await db.close()

        return photo


    async def update_photo(
        self,
        user_id,
        photo_order,
        file_id
    ):
        db = await self.connect()

        await db.execute("""
        UPDATE photos
        SET file_id = ?
        WHERE user_id = ?
        AND photo_order = ?
        """, (
            file_id,
            user_id,
            photo_order
        ))

        await db.commit()
        await db.close()


    async def delete_photo(
        self,
        user_id,
        photo_order
    ):
        db = await self.connect()

        await db.execute("""
        DELETE FROM photos
        WHERE user_id = ?
        AND photo_order = ?
        """, (
            user_id,
            photo_order
        ))

        await db.commit()
        await db.close()


    async def delete_all_photos(self, user_id):
        db = await self.connect()

        await db.execute("""
        DELETE FROM photos
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()
        await db.close()


    async def count_photos(self, user_id):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM photos
        WHERE user_id = ?
        """, (user_id,))

        count = await cursor.fetchone()

        await db.close()

        return count[0]
      async def add_like(self, from_user, to_user):
        db = await self.connect()

        await db.execute("""
        INSERT OR IGNORE INTO likes(
            from_user,
            to_user
        )
        VALUES(?,?)
        """, (
            from_user,
            to_user
        ))

        await db.commit()
        await db.close()


    async def remove_like(self, from_user, to_user):
        db = await self.connect()

        await db.execute("""
        DELETE FROM likes
        WHERE from_user = ?
        AND to_user = ?
        """, (
            from_user,
            to_user
        ))

        await db.commit()
        await db.close()


    async def is_liked(self, from_user, to_user):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT id
        FROM likes
        WHERE from_user = ?
        AND to_user = ?
        """, (
            from_user,
            to_user
        ))

        like = await cursor.fetchone()

        await db.close()

        return like is not None


    async def create_match(self, user1, user2):

        if user1 > user2:
            user1, user2 = user2, user1

        db = await self.connect()

        await db.execute("""
        INSERT OR IGNORE INTO matches(
            user1,
            user2
        )
        VALUES(?,?)
        """, (
            user1,
            user2
        ))

        await db.commit()
        await db.close()


    async def is_match(self, user1, user2):

        if user1 > user2:
            user1, user2 = user2, user1

        db = await self.connect()

        cursor = await db.execute("""
        SELECT id
        FROM matches
        WHERE user1 = ?
        AND user2 = ?
        """, (
            user1,
            user2
        ))

        match = await cursor.fetchone()

        await db.close()

        return match is not None


    async def get_matches(self, user_id):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT *
        FROM matches
        WHERE user1 = ?
        OR user2 = ?
        ORDER BY created_at DESC
        """, (
            user_id,
            user_id
        ))

        matches = await cursor.fetchall()

        await db.close()

        return matches


    async def get_random_profile(self, my_id):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT *
        FROM users
        WHERE user_id != ?
        AND banned = 0
        ORDER BY RANDOM()
        LIMIT 1
        """, (my_id,))

        user = await cursor.fetchone()

        await db.close()

        return user
      async def set_premium(self, user_id, premium=True):
        db = await self.connect()

        await db.execute("""
        UPDATE users
        SET premium = ?
        WHERE user_id = ?
        """, (
            1 if premium else 0,
            user_id
        ))

        await db.commit()
        await db.close()


    async def ban_user(self, user_id):
        db = await self.connect()

        await db.execute("""
        UPDATE users
        SET banned = 1
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()
        await db.close()


    async def unban_user(self, user_id):
        db = await self.connect()

        await db.execute("""
        UPDATE users
        SET banned = 0
        WHERE user_id = ?
        """, (user_id,))

        await db.commit()
        await db.close()


    async def report_user(self, from_user, to_user, reason):
        db = await self.connect()

        await db.execute("""
        INSERT INTO reports(
            from_user,
            to_user,
            reason
        )
        VALUES(?,?,?)
        """, (
            from_user,
            to_user,
            reason
        ))

        await db.commit()
        await db.close()


    async def get_reports(self):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT *
        FROM reports
        ORDER BY created_at DESC
        """)

        reports = await cursor.fetchall()

        await db.close()

        return reports


    async def count_users(self):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        """)

        count = await cursor.fetchone()

        await db.close()

        return count[0]


    async def count_premium(self):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE premium = 1
        """)

        count = await cursor.fetchone()

        await db.close()

        return count[0]


    async def count_matches(self):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM matches
        """)

        count = await cursor.fetchone()

        await db.close()

        return count[0]


    async def count_likes(self):
        db = await self.connect()

        cursor = await db.execute("""
        SELECT COUNT(*)
        FROM likes
        """)

        count = await cursor.fetchone()

        await db.close()

        return count[0]

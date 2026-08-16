import os
import psycopg2


def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL topilmadi")

    return psycopg2.connect(database_url)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # =========================
    # USERS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            age INTEGER,
            gender TEXT,
            bio TEXT,
            photo TEXT,
            city TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            premium_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            language TEXT DEFAULT 'uz',
            referred_by BIGINT,
            last_active TIMESTAMP DEFAULT NOW()
        )
    """)

    # Eski bazalar uchun migration
    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS city TEXT
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS premium_until TIMESTAMP
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'uz'
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS referred_by BIGINT
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS last_active TIMESTAMP DEFAULT NOW()
    """)

    # Eski foydalanuvchilarda NULL bo'lsa
    cur.execute("""
        UPDATE users
        SET last_active = COALESCE(last_active, created_at, NOW())
        WHERE last_active IS NULL
    """)

    # =========================
    # LIKES
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            from_user BIGINT,
            to_user BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # MATCHES
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            user1 BIGINT,
            user2 BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # REPORTS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            from_user BIGINT,
            to_user BIGINT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # BLOCKS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id SERIAL PRIMARY KEY,
            from_user BIGINT,
            to_user BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # MESSAGES
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            from_user BIGINT,
            to_user BIGINT,
            text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # PAYMENTS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount TEXT,
            days INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # PROFILE VIEWS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_views (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            viewed_user_id BIGINT,
            viewed_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # SKIPS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skips (
            id SERIAL PRIMARY KEY,
            from_user BIGINT,
            to_user BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # REFERRAL REWARDS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            referrals_count INTEGER NOT NULL,
            premium_days INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, referrals_count)
        )
    """)

    # =========================
    # NOTIFICATION LOGS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            notification_type TEXT NOT NULL,
            reference_id BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # =========================
    # INDEXLAR
    # =========================
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_city
        ON users(city)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_city_created
        ON users(city, created_at)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_last_active
        ON users(last_active)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notification_logs_user_type
        ON notification_logs(user_id, notification_type)
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_notification_logs_created
        ON notification_logs(created_at)
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database tayyor")

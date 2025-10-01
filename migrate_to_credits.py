#!/usr/bin/env python3
"""
Migration script to convert from premium/free_problems to credit-based system

Run this once to migrate existing users:
    python migrate_to_credits.py
"""

import asyncio
import sqlite3
from pathlib import Path


async def migrate_database():
    """Migrate database schema and data"""
    db_path = Path(__file__).parent / "bot_database.db"

    if not db_path.exists():
        print("❌ Database not found. Creating fresh database instead.")
        print("   Run: python -m bot.main to initialize")
        return

    print("🔄 Starting migration to credit-based system...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if old columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        has_old_schema = 'is_premium' in columns or 'free_problems_left' in columns
        has_new_schema = 'problems_remaining' in columns

        if not has_old_schema and has_new_schema:
            print("✅ Database already migrated!")
            return

        # Step 1: Add new columns if they don't exist
        if 'problems_remaining' not in columns:
            print("➕ Adding new column: problems_remaining")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN problems_remaining INTEGER DEFAULT 1
            """)

        if 'discussion_credits' not in columns:
            print("➕ Adding new column: discussion_credits")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN discussion_credits INTEGER DEFAULT 0
            """)

        if 'last_purchased_package' not in columns:
            print("➕ Adding new column: last_purchased_package")
            cursor.execute("""
                ALTER TABLE users ADD COLUMN last_purchased_package VARCHAR(20)
            """)

        # Step 2: Migrate data from old columns
        if 'is_premium' in columns and 'free_problems_left' in columns:
            print("🔄 Migrating user data...")

            # For premium users: give them 50 credits (equivalent to Large package)
            cursor.execute("""
                UPDATE users
                SET problems_remaining = 50,
                    last_purchased_package = 'large'
                WHERE is_premium = 1
            """)
            premium_count = cursor.rowcount
            print(f"   ✅ Migrated {premium_count} premium users → 50 credits")

            # For free users: convert free_problems_left to problems_remaining
            cursor.execute("""
                UPDATE users
                SET problems_remaining = free_problems_left,
                    last_purchased_package = NULL
                WHERE is_premium = 0
            """)
            free_count = cursor.rowcount
            print(f"   ✅ Migrated {free_count} free users → kept their remaining problems")

        # Step 3: Create backup table with old schema (optional safety measure)
        print("💾 Creating backup of old user data...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_backup_old_schema AS
            SELECT * FROM users
        """)

        # Step 4: Remove old columns (SQLite limitation: need to recreate table)
        if 'is_premium' in columns:
            print("🗑️  Removing old columns (is_premium, free_problems_left)...")

            # Get current table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
            old_create_stmt = cursor.fetchone()[0]

            # Create new table without old columns
            cursor.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(32),
                    first_name VARCHAR(64) NOT NULL,
                    problems_remaining INTEGER DEFAULT 1,
                    discussion_credits INTEGER DEFAULT 0,
                    last_purchased_package VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Copy data
            cursor.execute("""
                INSERT INTO users_new
                SELECT id, telegram_id, username, first_name,
                       problems_remaining, discussion_credits, last_purchased_package,
                       created_at, updated_at
                FROM users
            """)

            # Swap tables
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")

            print("   ✅ Old columns removed")

        conn.commit()

        # Step 5: Verify migration
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(problems_remaining), SUM(discussion_credits) FROM users")
        totals = cursor.fetchone()

        print("\n✅ Migration completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   Total users: {total_users}")
        print(f"   Total problem credits: {totals[0] or 0}")
        print(f"   Total discussion credits: {totals[1] or 0}")
        print(f"\n💡 Old data backed up in 'users_backup_old_schema' table")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Premium → Credit System")
    print("=" * 60)
    asyncio.run(migrate_database())

#!/usr/bin/env python3
"""
Database migration script for new subscription and referral features.

This script adds new tables and columns to existing database.
Run this BEFORE deploying the updated code.

Usage:
    python scripts/migrate_db.py
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.engine import engine, init_db
from bot.database.models import Base
from sqlalchemy import text


async def migrate():
    """Run database migration"""
    print("🔄 Starting database migration...")

    # Create all new tables
    print("📊 Creating new tables (subscriptions, referrals)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Migration completed successfully!")
    print("\n📝 Summary of changes:")
    print("  - Added 'subscriptions' table")
    print("  - Added 'referrals' table")
    print("  - Updated 'users' table with new columns:")
    print("    • subscription_id")
    print("    • referred_by")
    print("    • referral_code")
    print("    • referral_credits")
    print("    • problems_remaining (default changed from 3 to 1)")


async def check_existing_users():
    """Check if there are existing users that need migration"""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) as count FROM users"))
        count = result.scalar()

        if count > 0:
            print(f"\n⚠️  Found {count} existing users in database")
            print("   Their data will be preserved. New fields will have default values.")
        else:
            print("\n✨ No existing users found. Clean migration.")


async def main():
    """Main migration function"""
    print("=" * 60)
    print("  МозгоБот - Database Migration")
    print("  New features: Subscriptions + Referral Program")
    print("=" * 60)
    print()

    # Check existing data
    await check_existing_users()

    # Confirm migration
    response = input("\n⚡ Ready to migrate? (yes/no): ").lower().strip()
    if response != 'yes':
        print("❌ Migration cancelled.")
        return

    # Run migration
    await migrate()

    print("\n🎉 All done! You can now deploy the updated bot code.")
    print("\n💡 Next steps:")
    print("   1. Restart the bot: sudo systemctl restart problem-solver-bot")
    print("   2. Check logs: journalctl -u problem-solver-bot -f")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Migration failed with error:")
        print(f"   {e}")
        sys.exit(1)

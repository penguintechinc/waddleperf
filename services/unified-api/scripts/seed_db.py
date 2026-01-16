#!/usr/bin/env python3
"""Seed database with default admin user and test data."""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from database.connection import get_dal
from config import Config


def seed_admin_user(db):
    """Create default admin user if not exists."""
    existing = db(db.users.email == 'admin@localhost.local').select().first()
    if existing:
        print(f"Admin user already exists (id={existing.id})")
        # Update password to standard
        password_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        db(db.users.id == existing.id).update(password_hash=password_hash)
        db.commit()
        print("Password reset to: admin123")
        return existing.id

    password_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    user_id = db.users.insert(
        email='admin@localhost.local',
        username='admin',
        password_hash=password_hash,
        first_name='Admin',
        last_name='User',
        is_active='T',
        role='admin',
        mfa_enabled='F'
    )
    db.commit()
    print(f"Created admin user (id={user_id})")
    print("  Email: admin@localhost.local")
    print("  Password: admin123")
    return user_id


def main():
    """Main seed function."""
    print("Seeding WaddlePerf database...")

    config = Config()
    db = get_dal(config)

    seed_admin_user(db)

    print("\nDatabase seeding complete!")
    print("\nDefault credentials:")
    print("  Email: admin@localhost.local")
    print("  Password: admin123")


if __name__ == '__main__':
    main()

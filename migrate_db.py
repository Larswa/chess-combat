#!/usr/bin/env python3
"""
Database migration script for Chess Combat
Creates all necessary database tables and performs any required migrations.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.db.models import Base

def migrate_database(database_url: str = None):
    """
    Create all database tables and perform migrations.

    Args:
        database_url: Database URL. If None, uses DATABASE_URL environment variable.

    Returns:
        bool: True if migration successful, False otherwise
    """
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: No database URL provided. Set DATABASE_URL environment variable.")
        return False

    print(f"Migrating database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    try:
        # Create engine with appropriate settings for different database types
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        engine = create_engine(database_url, connect_args=connect_args)

        # Test database connection
        with engine.connect() as conn:
            # For SQLite, enable foreign keys
            if database_url.startswith("sqlite"):
                conn.execute(text("PRAGMA foreign_keys=ON"))

            print("Database connection established successfully.")

        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Verify tables were created
        with engine.connect() as conn:
            if database_url.startswith("sqlite"):
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            else:
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))

            tables = [row[0] for row in result.fetchall()]
            print(f"Created tables: {', '.join(tables)}")

        print("Database migration completed successfully!")
        return True

    except SQLAlchemyError as e:
        print(f"Database migration failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        return False

def main():
    """Main entry point for the migration script."""
    import argparse

    parser = argparse.ArgumentParser(description="Chess Combat Database Migration")
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides DATABASE_URL environment variable)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if migration is needed without performing it"
    )

    args = parser.parse_args()

    database_url = args.database_url or os.getenv("DATABASE_URL")

    if args.check:
        # Check if tables exist
        try:
            connect_args = {}
            if database_url.startswith("sqlite"):
                connect_args = {"check_same_thread": False}

            engine = create_engine(database_url, connect_args=connect_args)

            with engine.connect() as conn:
                if database_url.startswith("sqlite"):
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('players', 'games', 'moves')"))
                else:
                    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('players', 'games', 'moves')"))

                existing_tables = [row[0] for row in result.fetchall()]
                required_tables = ['players', 'games', 'moves']
                missing_tables = [t for t in required_tables if t not in existing_tables]

                if missing_tables:
                    print(f"Migration needed. Missing tables: {', '.join(missing_tables)}")
                    sys.exit(1)
                else:
                    print("All required tables exist. No migration needed.")
                    sys.exit(0)

        except Exception as e:
            print(f"Error checking database: {e}")
            sys.exit(1)
    else:
        # Perform migration
        success = migrate_database(database_url)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

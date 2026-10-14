"""
Database Initialization Script for AI Student Learning Mentor.
Executes database/schema.sql using PyMySQL against the running MySQL instance (XAMPP).
Does not launch or manage any server processes.
"""
import sys
import os

# Add parent directory to path so services can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import REQUIRED_TABLES, initialize_database, check_db_health


def main():
    print("=" * 60)
    print("AI Student Learning Mentor - Database Initialization")
    print("=" * 60)
    print("Connecting to MySQL and executing schema.sql...")

    success, message = initialize_database()
    if not success:
        print(f"[ERROR] Database initialization failed: {message}")
        sys.exit(1)

    print(f"[SUCCESS] {message}")
    print("\nRunning health verification check:")
    health = check_db_health()
    print(f"- Connected: {health['connected']}")
    print(f"- Database Exists: {health['database_exists']} ({health['database_name']})")
    expected_tables = len(REQUIRED_TABLES)
    print(f"- Tables Found: {len(health.get('tables_found', []))} of {expected_tables} required")
    if health.get('all_required_tables_present'):
        print(f"[SUCCESS] All {expected_tables} required tables exist with valid schema!")
    else:
        print(f"[WARNING] Missing tables: {health.get('missing_tables')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

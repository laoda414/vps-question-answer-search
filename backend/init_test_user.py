"""
Initialize test user for development
This script creates a test user if TEST_USERNAME and TEST_PASSWORD are set in .env
"""

import sys
from config import config
from database import db

def init_test_user():
    """Create test user if configured"""
    if not config.TEST_USERNAME or not config.TEST_PASSWORD:
        print("⚠️  No test credentials configured in .env")
        print("   Set TEST_USERNAME and TEST_PASSWORD to auto-create test user")
        return False

    try:
        # Check if user already exists
        existing_user = db.get_user_by_username(config.TEST_USERNAME)
        if existing_user:
            print(f"✅ Test user '{config.TEST_USERNAME}' already exists")
            return True

        # Create test user
        db.create_user(config.TEST_USERNAME, config.TEST_PASSWORD)
        print(f"✅ Test user created successfully!")
        print(f"   Username: {config.TEST_USERNAME}")
        print(f"   Password: {config.TEST_PASSWORD}")
        print()
        print("⚠️  REMEMBER: Remove TEST_USERNAME and TEST_PASSWORD from .env before deployment!")
        return True

    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Test User Initialization")
    print("=" * 60)

    if init_test_user():
        sys.exit(0)
    else:
        sys.exit(1)

#!/usr/bin/env python
"""
Check Current Database Connection
ตรวจสอบการเชื่อมต่อฐานข้อมูลปัจจุบัน
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')
import django
django.setup()

from django.conf import settings
from django.db import connection

def check_database():
    """ตรวจสอบการเชื่อมต่อฐานข้อมูล"""

    print("=" * 70)
    print("  Database Connection Status")
    print("=" * 70)
    print()

    # Database settings
    db_config = settings.DATABASES['default']

    print("📊 Database Configuration:")
    print(f"   Engine:   {db_config['ENGINE']}")
    print(f"   Name:     {db_config['NAME']}")
    print(f"   User:     {db_config['USER']}")
    print(f"   Host:     {db_config['HOST']}")
    print(f"   Port:     {db_config['PORT']}")
    print()

    # Test connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]

            print("✅ Connection Status: Connected")
            print(f"📁 Current Database: {current_db}")
            print()

            # Count tables
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s
            """, [current_db])
            table_count = cursor.fetchone()[0]

            print(f"📋 Total Tables: {table_count}")
            print()

            # Count records in main tables
            from apps.accounts.models import User, Department
            from apps.registry.models import StaffProfile, BadgeRequest
            from apps.badges.models import Badge

            print("📊 Data Summary:")
            print(f"   Users:         {User.objects.count()}")
            print(f"   Departments:   {Department.objects.count()}")
            print(f"   Staff:         {StaffProfile.objects.count()}")
            print(f"   Requests:      {BadgeRequest.objects.count()}")
            print(f"   Badges:        {Badge.objects.count()}")
            print()

            # Environment
            print("⚙️  Environment:")
            print(f"   DEBUG:         {settings.DEBUG}")
            print(f"   SECRET_KEY:    {settings.SECRET_KEY[:10]}..." if settings.SECRET_KEY else "   SECRET_KEY:    Not Set")

            # Determine which database we're using
            if 'production' in current_db.lower():
                print()
                print("🟢 Mode: PRODUCTION")
                print("   ⚠️  Make sure DEBUG=False for production!")
            else:
                print()
                print("🔵 Mode: DEVELOPMENT")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

    print()
    print("=" * 70)
    return True

if __name__ == '__main__':
    check_database()

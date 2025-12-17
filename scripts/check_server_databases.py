#!/usr/bin/env python
"""
ตรวจสอบฐานข้อมูลทั้งหมดบน MySQL Server
Check all databases on MySQL Server
"""
import MySQLdb
from decouple import config

def check_databases():
    """แสดงฐานข้อมูลทั้งหมดบน server"""

    # ข้อมูลการเชื่อมต่อ
    host = config('DB_HOST')
    port = int(config('DB_PORT', default='3306'))
    user = config('DB_USER')
    password = config('DB_PASSWORD')

    print("=" * 70)
    print("  ตรวจสอบฐานข้อมูลทั้งหมดบน MySQL Server")
    print("=" * 70)
    print()
    print(f"📡 Server: {host}:{port}")
    print(f"👤 User: {user}")
    print()

    try:
        # เชื่อมต่อ MySQL
        conn = MySQLdb.connect(
            host=host,
            port=port,
            user=user,
            passwd=password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        print("✅ เชื่อมต่อสำเร็จ!")
        print()

        # แสดงฐานข้อมูลทั้งหมด
        print("📊 รายการฐานข้อมูลทั้งหมด:")
        print("-" * 70)

        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()

        for i, db in enumerate(databases, 1):
            db_name = db[0]

            # นับตารางในแต่ละฐาน
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (db_name,))
            table_count = cursor.fetchone()[0]

            # เช็คว่าเป็นฐานของเรา
            marker = ""
            if 'ceremony' in db_name.lower():
                marker = " ⭐ [CeremonyBadge System]"

            print(f"{i:2}. {db_name:30} ({table_count:3} tables){marker}")

        print("-" * 70)
        print()

        # เช็คว่ามีฐาน CeremonyBadge_Production หรือไม่
        cursor.execute("SHOW DATABASES LIKE 'CeremonyBadge_Production'")
        result = cursor.fetchone()

        if result:
            print("✅ พบฐาน CeremonyBadge_Production")

            # แสดงรายละเอียด
            cursor.execute("""
                SELECT
                    table_name,
                    table_rows
                FROM information_schema.tables
                WHERE table_schema = 'CeremonyBadge_Production'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            print(f"\n📋 ตารางในฐาน CeremonyBadge_Production ({len(tables)} ตาราง):")
            print("-" * 70)
            for table_name, row_count in tables:
                print(f"   - {table_name:30} ({row_count if row_count else 0:5} rows)")
            print("-" * 70)

        else:
            print("❌ ไม่พบฐาน CeremonyBadge_Production")
            print()
            print("🔍 ลองเช็คด้วยชื่อแบบ case-insensitive:")

            cursor.execute("SHOW DATABASES")
            all_dbs = cursor.fetchall()

            found = False
            for db in all_dbs:
                if 'production' in db[0].lower() or 'ceremony' in db[0].lower():
                    print(f"   ✓ พบ: {db[0]}")
                    found = True

            if not found:
                print("   ❌ ไม่พบฐานที่เกี่ยวข้อง")

        cursor.close()
        conn.close()

    except MySQLdb.Error as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

    print()
    print("=" * 70)

if __name__ == '__main__':
    check_databases()

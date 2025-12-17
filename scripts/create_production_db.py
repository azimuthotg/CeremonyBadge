#!/usr/bin/env python
"""
สร้างฐานข้อมูล Production
Create CeremonyBadge_Production database
"""
import MySQLdb
from decouple import config

def create_production_database():
    """สร้างฐานข้อมูล CeremonyBadge_Production"""

    # ข้อมูลการเชื่อมต่อ
    host = config('DB_HOST')
    port = int(config('DB_PORT', default='3306'))
    user = config('DB_USER')
    password = config('DB_PASSWORD')

    print(f"📡 กำลังเชื่อมต่อ MySQL Server: {host}:{port}")
    print(f"👤 User: {user}")

    try:
        # เชื่อมต่อ MySQL (ไม่ระบุ database)
        conn = MySQLdb.connect(
            host=host,
            port=port,
            user=user,
            passwd=password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        print(f"✅ เชื่อมต่อสำเร็จ!")

        # ตรวจสอบว่ามีฐาน CeremonyBadge_Production อยู่แล้วหรือไม่
        cursor.execute("SHOW DATABASES LIKE 'CeremonyBadge_Production'")
        result = cursor.fetchone()

        if result:
            print(f"⚠️  พบฐานข้อมูล CeremonyBadge_Production อยู่แล้ว")
            response = input("ต้องการลบและสร้างใหม่หรือไม่? (yes/no): ")

            if response.lower() in ['yes', 'y']:
                print(f"🗑️  กำลังลบฐานข้อมูลเดิม...")
                cursor.execute("DROP DATABASE CeremonyBadge_Production")
                print(f"✅ ลบฐานเดิมเรียบร้อย")
            else:
                print(f"❌ ยกเลิกการสร้างฐานใหม่")
                cursor.close()
                conn.close()
                return False

        # สร้างฐานข้อมูลใหม่
        print(f"🔨 กำลังสร้างฐานข้อมูล CeremonyBadge_Production...")

        cursor.execute("""
            CREATE DATABASE CeremonyBadge_Production
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)

        print(f"✅ สร้างฐานข้อมูล CeremonyBadge_Production สำเร็จ!")

        # แสดงรายการฐานข้อมูลทั้งหมด
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()

        print(f"\n📊 รายการฐานข้อมูลทั้งหมด:")
        for db in databases:
            marker = " ✓" if db[0] == 'CeremonyBadge_Production' else ""
            print(f"   - {db[0]}{marker}")

        cursor.close()
        conn.close()

        return True

    except MySQLdb.Error as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("  สร้างฐานข้อมูล Production")
    print("  CeremonyBadge_Production")
    print("=" * 60)
    print()

    success = create_production_database()

    print()
    print("=" * 60)
    if success:
        print("✅ เสร็จสิ้น! พร้อมสำหรับขั้นตอนถัดไป")
    else:
        print("❌ การสร้างฐานข้อมูลล้มเหลว")
    print("=" * 60)

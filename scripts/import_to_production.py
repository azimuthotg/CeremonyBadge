#!/usr/bin/env python
"""
Import Data to Production Database
นำเข้าข้อมูลจาก backup เข้าสู่ CeremonyBadge_Production
"""
import os
import sys
import subprocess
import shutil
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def import_to_production():
    """Import data from backup to production database"""

    print("=" * 70)
    print("  Import Data to Production Database")
    print("  CeremonyBadge_Production")
    print("=" * 70)
    print()

    # หา backup file ล่าสุด
    backup_dir = os.path.join(BASE_DIR, 'backups')
    backup_files = glob.glob(os.path.join(backup_dir, 'CeremonyBadge_backup_*.json'))

    if not backup_files:
        print("❌ ไม่พบไฟล์ backup!")
        return False

    # เรียงตามเวลา (ใหม่สุดก่อน)
    backup_files.sort(reverse=True)
    latest_backup = backup_files[0]

    print(f"📁 Backup file: {os.path.basename(latest_backup)}")
    file_size = os.path.getsize(latest_backup) / (1024 * 1024)
    print(f"📊 Size: {file_size:.2f} MB")
    print()

    # Backup .env เดิม
    env_file = os.path.join(BASE_DIR, '.env')
    env_backup = os.path.join(BASE_DIR, '.env.backup_temp')

    print("📋 Step 1: Backup current .env file")
    if os.path.exists(env_file):
        shutil.copy2(env_file, env_backup)
        print(f"   ✅ Backed up to: .env.backup_temp")

    # Copy .env.production เป็น .env
    env_production = os.path.join(BASE_DIR, '.env.production')

    print("📋 Step 2: Switch to production .env")
    if os.path.exists(env_production):
        shutil.copy2(env_production, env_file)
        print(f"   ✅ Using .env.production")
    else:
        print(f"   ❌ .env.production not found!")
        return False

    try:
        print("📋 Step 3: Import data to production database")
        print(f"   กำลัง import จาก {os.path.basename(latest_backup)}...")
        print()

        # Run loaddata
        result = subprocess.run(
            [sys.executable, 'manage.py', 'loaddata', latest_backup],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print(f"   ❌ Import failed!")
            return False

        print()
        print("   ✅ Data imported successfully!")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    finally:
        # Restore .env เดิม
        print()
        print("📋 Step 4: Restore original .env")
        if os.path.exists(env_backup):
            shutil.copy2(env_backup, env_file)
            os.remove(env_backup)
            print(f"   ✅ Restored original .env")

if __name__ == '__main__':
    success = import_to_production()

    print()
    print("=" * 70)
    if success:
        print("✅ All data imported to CeremonyBadge_Production successfully!")
        print()
        print("📝 หมายเหตุ: ข้อมูลถูก copy ทั้งหมดแล้ว")
        print("   สามารถลบข้อมูลทดสอบออกได้ผ่าน Django Admin")
    else:
        print("❌ Import failed!")
    print("=" * 70)

    sys.exit(0 if success else 1)

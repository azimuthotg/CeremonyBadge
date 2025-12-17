#!/usr/bin/env python
"""
Backup CeremonyBadge Database
สคริปต์สำหรับสำรองฐานข้อมูล CeremonyBadge
"""
import os
import sys
import subprocess
from datetime import datetime

# เพิ่ม path ของ Django project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')
import django
django.setup()

from django.conf import settings

def backup_database():
    """Backup database using Django dumpdata"""

    # สร้างโฟลเดอร์ backups
    backup_dir = os.path.join(BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    # สร้างชื่อไฟล์ backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'CeremonyBadge_backup_{timestamp}.json')

    print(f"🔄 กำลัง Backup ฐานข้อมูล CeremonyBadge...")
    print(f"📁 ไฟล์: {backup_file}")

    # ใช้ Django dumpdata
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            subprocess.run(
                [sys.executable, 'manage.py', 'dumpdata',
                 '--natural-foreign', '--natural-primary',
                 '--indent', '2'],
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
                cwd=BASE_DIR
            )

        file_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
        print(f"✅ Backup สำเร็จ!")
        print(f"📊 ขนาดไฟล์: {file_size:.2f} MB")
        print(f"💾 บันทึกที่: {backup_file}")

        return backup_file

    except subprocess.CalledProcessError as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        if e.stderr:
            print(e.stderr.decode())
        return None
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return None

if __name__ == '__main__':
    backup_database()

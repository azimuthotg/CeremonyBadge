#!/usr/bin/env python
"""
Clear All Staff Data (Keep Settings)
ลบข้อมูลบุคลากรทั้งหมด (เก็บข้อมูลตั้งค่าไว้)
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')
import django
django.setup()

from django.db import connection
from apps.registry.models import StaffProfile, Photo, BadgeRequest
from apps.badges.models import Badge, PrintLog
from apps.approvals.models import ApprovalLog
from apps.accounts.models import User

def clear_staff_data():
    """ลบข้อมูลบุคลากรทั้งหมด แต่เก็บข้อมูลตั้งค่า"""

    print("=" * 70)
    print("  ⚠️  ลบข้อมูลบุคลากรทั้งหมด")
    print("  Clear All Staff Data (Keep Settings)")
    print("=" * 70)
    print()

    # แสดงฐานข้อมูลปัจจุบัน
    cursor = connection.cursor()
    cursor.execute('SELECT DATABASE()')
    db_name = cursor.fetchone()[0]

    print(f"📊 Database: {db_name}")
    print()

    # นับข้อมูลก่อนลบ
    print("📋 ข้อมูลปัจจุบัน (ก่อนลบ):")
    print("-" * 70)

    staff_count = StaffProfile.objects.count()
    photo_count = Photo.objects.count()
    request_count = BadgeRequest.objects.count()
    badge_count = Badge.objects.count()
    print_log_count = PrintLog.objects.count()
    approval_log_count = ApprovalLog.objects.count()

    print(f"   Staff Profiles:    {staff_count:5} รายการ")
    print(f"   Photos:            {photo_count:5} รายการ")
    print(f"   Badge Requests:    {request_count:5} รายการ")
    print(f"   Badges:            {badge_count:5} รายการ")
    print(f"   Print Logs:        {print_log_count:5} รายการ")
    print(f"   Approval Logs:     {approval_log_count:5} รายการ")
    print("-" * 70)

    total_records = (staff_count + photo_count + request_count +
                     badge_count + print_log_count + approval_log_count)

    print(f"   📊 รวมทั้งหมด:      {total_records:5} รายการ")
    print()

    # ข้อมูลที่จะเก็บไว้
    print("✅ ข้อมูลที่จะเก็บไว้:")
    print("-" * 70)
    from apps.accounts.models import Department
    from apps.badges.models import BadgeType
    from apps.registry.models import Zone
    from apps.settings_app.models import SystemSetting

    dept_count = Department.objects.count()
    badge_type_count = BadgeType.objects.count()
    zone_count = Zone.objects.count()
    setting_count = SystemSetting.objects.count()
    admin_count = User.objects.filter(role__in=['admin', 'officer']).count()

    print(f"   Departments:       {dept_count:5} หน่วยงาน")
    print(f"   Badge Types:       {badge_type_count:5} ประเภทบัตร")
    print(f"   Zones:             {zone_count:5} โซน")
    print(f"   System Settings:   {setting_count:5} การตั้งค่า")
    print(f"   Admin/Officer:     {admin_count:5} บัญชี (ไม่ลบ)")
    print("-" * 70)
    print()

    # ยืนยันการลบ
    print("⚠️  คำเตือน: การดำเนินการนี้จะลบข้อมูลดังต่อไปนี้:")
    print("   - บุคลากรทั้งหมด (Staff Profiles)")
    print("   - รูปภาพทั้งหมด (Photos)")
    print("   - คำขอบัตรทั้งหมด (Badge Requests)")
    print("   - บัตรที่ออกแล้วทั้งหมด (Badges)")
    print("   - บันทึกการพิมพ์ (Print Logs)")
    print("   - บันทึกการอนุมัติ (Approval Logs)")
    print("   - User ที่เป็น Submitter (ไม่ลบ Admin/Officer)")
    print()
    print("✅ จะเก็บไว้:")
    print("   - หน่วยงาน (Departments)")
    print("   - ประเภทบัตร (Badge Types)")
    print("   - โซนปฏิบัติงาน (Zones)")
    print("   - การตั้งค่าระบบ (System Settings)")
    print("   - User ที่เป็น Admin/Officer")
    print()

    # ขอยืนยัน 2 ครั้ง
    print("=" * 70)
    response1 = input("⚠️  ยืนยันการลบข้อมูล? พิมพ์ 'YES' เพื่อดำเนินการ: ")

    if response1 != 'YES':
        print("❌ ยกเลิกการลบข้อมูล")
        return False

    print()
    response2 = input("⚠️  ยืนยันอีกครั้ง? พิมพ์ 'DELETE' เพื่อดำเนินการ: ")

    if response2 != 'DELETE':
        print("❌ ยกเลิกการลบข้อมูล")
        return False

    print()
    print("=" * 70)
    print("🗑️  กำลังลบข้อมูล...")
    print()

    try:
        # ลบตามลำดับ (เพื่อหลีกเลี่ยง Foreign Key constraints)

        # 1. Print Logs
        print("1/7 ลบ Print Logs...", end=" ")
        deleted_print = PrintLog.objects.all().delete()
        print(f"✅ ลบ {deleted_print[0]} รายการ")

        # 2. Approval Logs
        print("2/7 ลบ Approval Logs...", end=" ")
        deleted_approval = ApprovalLog.objects.all().delete()
        print(f"✅ ลบ {deleted_approval[0]} รายการ")

        # 3. Badges
        print("3/7 ลบ Badges...", end=" ")
        deleted_badges = Badge.objects.all().delete()
        print(f"✅ ลบ {deleted_badges[0]} รายการ")

        # 4. Badge Requests
        print("4/7 ลบ Badge Requests...", end=" ")
        deleted_requests = BadgeRequest.objects.all().delete()
        print(f"✅ ลบ {deleted_requests[0]} รายการ")

        # 5. Photos
        print("5/7 ลบ Photos...", end=" ")
        deleted_photos = Photo.objects.all().delete()
        print(f"✅ ลบ {deleted_photos[0]} รายการ")

        # 6. Staff Profiles
        print("6/7 ลบ Staff Profiles...", end=" ")
        deleted_staff = StaffProfile.objects.all().delete()
        print(f"✅ ลบ {deleted_staff[0]} รายการ")

        # 7. Submitter Users (เก็บ Admin/Officer ไว้)
        print("7/7 ลบ Submitter Users...", end=" ")
        deleted_users = User.objects.filter(role='submitter').delete()
        print(f"✅ ลบ {deleted_users[0]} รายการ")

        print()
        print("=" * 70)
        print("✅ ลบข้อมูลสำเร็จ!")
        print()

        # แสดงข้อมูลหลังลบ
        print("📊 ข้อมูลหลังลบ:")
        print("-" * 70)
        print(f"   Staff Profiles:    {StaffProfile.objects.count():5} รายการ")
        print(f"   Photos:            {Photo.objects.count():5} รายการ")
        print(f"   Badge Requests:    {BadgeRequest.objects.count():5} รายการ")
        print(f"   Badges:            {Badge.objects.count():5} รายการ")
        print(f"   Print Logs:        {PrintLog.objects.count():5} รายการ")
        print(f"   Approval Logs:     {ApprovalLog.objects.count():5} รายการ")
        print("-" * 70)
        print()

        print("✅ ข้อมูลที่เก็บไว้:")
        print("-" * 70)
        print(f"   Departments:       {Department.objects.count():5} หน่วยงาน")
        print(f"   Badge Types:       {BadgeType.objects.count():5} ประเภทบัตร")
        print(f"   Zones:             {Zone.objects.count():5} โซน")
        print(f"   System Settings:   {SystemSetting.objects.count():5} การตั้งค่า")
        print(f"   Admin/Officer:     {User.objects.filter(role__in=['admin', 'officer']).count():5} บัญชี")
        print("-" * 70)

        return True

    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == '__main__':
    print()
    success = clear_staff_data()

    print()
    print("=" * 70)
    if success:
        print("✅ เสร็จสิ้น! พร้อมลงทะเบียนบุคลากรใหม่")
        print()
        print("📝 หมายเหตุ:")
        print("   - ข้อมูลหน่วยงาน, ประเภทบัตร, โซน ยังคงอยู่")
        print("   - สามารถเริ่มลงทะเบียนบุคลากรใหม่ได้ทันที")
        print("   - บัญชี Admin/Officer ยังใช้งานได้ตามปกติ")
    else:
        print("❌ การลบข้อมูลล้มเหลวหรือถูกยกเลิก")
    print("=" * 70)
    print()

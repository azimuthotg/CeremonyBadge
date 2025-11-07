#!/usr/bin/env python
"""
สคริปต์สร้างข้อมูลเริ่มต้นสำหรับระบบ NPU-CeremonyBadge
รัน: python create_initial_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')
django.setup()

from apps.accounts.models import Department, User
from apps.badges.models import BadgeType, BadgeTemplate
from apps.registry.models import Zone
from datetime import date

def create_departments():
    """สร้างหน่วยงานเริ่มต้น"""
    print("\n" + "="*50)
    print("สร้างหน่วยงาน...")
    print("="*50)

    dept, created = Department.objects.get_or_create(
        code='NPU',
        defaults={
            'name': 'มหาวิทยาลัยนครพนม',
            'description': 'หน่วยงานหลัก',
            'is_active': True
        }
    )

    if created:
        print(f"✓ สร้างหน่วยงานใหม่: {dept.name}")
    else:
        print(f"→ หน่วยงานมีอยู่แล้ว: {dept.name}")

    return dept


def create_badge_types():
    """สร้างประเภทบัตร 4 สี"""
    print("\n" + "="*50)
    print("สร้างประเภทบัตร...")
    print("="*50)

    badge_types_data = [
        {
            'name': 'บัตรชมพู',
            'color': 'pink',
            'color_code': '#FFC0CB',
            'description': 'บุคลากรชั้นในสุด - ผู้ที่ปฏิบัติงานใกล้ชิดพระองค์'
        },
        {
            'name': 'บัตรแดง',
            'color': 'red',
            'color_code': '#FF6B6B',
            'description': 'บุคลากรชั้นใน - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นใน'
        },
        {
            'name': 'บัตรเหลือง',
            'color': 'yellow',
            'color_code': '#FFD93D',
            'description': 'บุคลากรชั้นกลาง - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นกลาง'
        },
        {
            'name': 'บัตรเขียว',
            'color': 'green',
            'color_code': '#6BCB77',
            'description': 'บุคลากรชั้นนอก - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นนอก'
        },
    ]

    badge_types = []
    for bt_data in badge_types_data:
        bt, created = BadgeType.objects.get_or_create(
            color=bt_data['color'],
            defaults=bt_data
        )

        if created:
            print(f"✓ สร้างประเภทบัตรใหม่: {bt.name} ({bt.color_code})")
        else:
            print(f"→ ประเภทบัตรมีอยู่แล้ว: {bt.name}")

        badge_types.append(bt)

    return badge_types


def create_badge_templates(badge_types):
    """สร้างแม่แบบบัตรสำหรับแต่ละประเภท"""
    print("\n" + "="*50)
    print("สร้างแม่แบบบัตร...")
    print("="*50)

    for bt in badge_types:
        template, created = BadgeTemplate.objects.get_or_create(
            badge_type=bt,
            defaults={
                'background_color': bt.color_code,
                'text_color': '#000000',
                'logo_position_x': 50,
                'logo_position_y': 20,
                'photo_position_x': 50,
                'photo_position_y': 100,
                'qr_position_x': 150,
                'qr_position_y': 250,
                'is_active': True
            }
        )

        if created:
            print(f"✓ สร้างแม่แบบบัตรใหม่: {bt.name}")
        else:
            print(f"→ แม่แบบบัตรมีอยู่แล้ว: {bt.name}")


def create_zones():
    """สร้างโซนปฏิบัติงาน"""
    print("\n" + "="*50)
    print("สร้างโซนปฏิบัติงาน...")
    print("="*50)

    zones_data = [
        {
            'code': 'A',
            'name': 'กอร.ถปภ. ณ มหาวิทยาลัยนครพนม',
            'description': 'พื้นที่ภายในมหาวิทยาลัยนครพนม - โซน A',
            'order': 1,
            'is_active': True
        },
        {
            'code': 'B',
            'name': 'กอร.ถปภ. ณ ท่าอากาศยานนครพนม',
            'description': 'พื้นที่ท่าอากาศยานนครพนม - โซน B',
            'order': 2,
            'is_active': True
        },
        {
            'code': 'C',
            'name': 'กอร.ถปภ. ณ จุดตรวจ',
            'description': 'พื้นที่จุดตรวจต่างๆ - โซน C',
            'order': 3,
            'is_active': True
        },
    ]

    for zone_data in zones_data:
        zone, created = Zone.objects.get_or_create(
            code=zone_data['code'],
            defaults=zone_data
        )

        if created:
            print(f"✓ สร้างโซนใหม่: {zone.code} - {zone.name}")
        else:
            print(f"→ โซนมีอยู่แล้ว: {zone.code} - {zone.name}")


def create_system_settings():
    """สร้างการตั้งค่าระบบเริ่มต้น"""
    print("\n" + "="*50)
    print("สร้างการตั้งค่าระบบ...")
    print("="*50)

    from apps.settings_app.models import SystemSetting

    settings_data = [
        {
            'key': 'qr_secret_key',
            'value': 'ceremony_badge_npu_2567',
            'setting_type': 'string',
            'description': 'Secret Key สำหรับสร้าง HMAC Signature ของ QR Code'
        },
        {
            'key': 'primary_color',
            'value': '#A78BFA',
            'setting_type': 'color',
            'description': 'สีหลักของระบบ (ม่วงพาสเทล)'
        },
        {
            'key': 'university_name',
            'value': 'มหาวิทยาลัยนครพนม',
            'setting_type': 'string',
            'description': 'ชื่อมหาวิทยาลัย'
        },
        {
            'key': 'ceremony_year',
            'value': '2567',
            'setting_type': 'string',
            'description': 'ปีพุทธศักราชของพิธี'
        },
        {
            'key': 'auto_approve',
            'value': 'false',
            'setting_type': 'boolean',
            'description': 'อนุมัติอัตโนมัติ (ไม่แนะนำ)'
        },
        {
            'key': 'work_start_date',
            'value': '2025-12-01',
            'setting_type': 'string',
            'description': 'วันที่เริ่มต้นปฏิบัติงาน (รูปแบบ YYYY-MM-DD)'
        },
        {
            'key': 'work_end_date',
            'value': '2025-12-15',
            'setting_type': 'string',
            'description': 'วันที่สิ้นสุดการปฏิบัติงาน (รูปแบบ YYYY-MM-DD)'
        },
    ]

    for setting_data in settings_data:
        setting, created = SystemSetting.objects.get_or_create(
            key=setting_data['key'],
            defaults=setting_data
        )

        if created:
            print(f"✓ สร้างการตั้งค่าใหม่: {setting.key}")
        else:
            print(f"→ การตั้งค่ามีอยู่แล้ว: {setting.key}")


def main():
    """ฟังก์ชันหลัก"""
    print("\n" + "="*50)
    print("🚀 เริ่มสร้างข้อมูลเริ่มต้น")
    print("="*50)

    try:
        # 1. สร้างหน่วยงาน
        dept = create_departments()

        # 2. สร้างประเภทบัตร
        badge_types = create_badge_types()

        # 3. สร้างแม่แบบบัตร
        create_badge_templates(badge_types)

        # 4. สร้างโซนปฏิบัติงาน
        create_zones()

        # 5. สร้างการตั้งค่าระบบ
        create_system_settings()

        print("\n" + "="*50)
        print("✅ สร้างข้อมูลเริ่มต้นเรียบร้อยแล้ว!")
        print("="*50)
        print("\nข้อมูลที่สร้าง:")
        print(f"  - หน่วยงาน: {Department.objects.count()} รายการ")
        print(f"  - ประเภทบัตร: {BadgeType.objects.count()} ประเภท")
        print(f"  - แม่แบบบัตร: {BadgeTemplate.objects.count()} แม่แบบ")
        print(f"  - โซนปฏิบัติงาน: {Zone.objects.count()} โซน")
        print(f"  - การตั้งค่าระบบ: {SystemSetting.objects.count()} รายการ")
        print("\nขั้นตอนต่อไป:")
        print("  1. สร้าง superuser: python manage.py createsuperuser")
        print("  2. รันเซิร์ฟเวอร์: python manage.py runserver")
        print("  3. เข้าระบบ Admin: http://127.0.0.1:8000/admin")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    from apps.settings_app.models import SystemSetting
    main()

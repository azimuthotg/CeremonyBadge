#!/usr/bin/env python
"""
อัปเดตคำอธิบายของประเภทบัตร
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')
django.setup()

from apps.badges.models import BadgeType

# อัปเดตคำอธิบาย
badge_descriptions = {
    'pink': 'บุคลากรชั้นในสุด - ผู้ที่ปฏิบัติงานใกล้ชิดพระองค์',
    'red': 'บุคลากรชั้นใน - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นใน',
    'yellow': 'บุคลากรชั้นกลาง - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นกลาง',
    'green': 'บุคลากรชั้นนอก - ผู้ที่ปฏิบัติงานในพื้นที่ชั้นนอก',
}

print("อัปเดตคำอธิบายประเภทบัตร...")
for color, description in badge_descriptions.items():
    try:
        badge_type = BadgeType.objects.get(color=color)
        badge_type.description = description
        badge_type.save()
        print(f"✓ อัปเดต: {badge_type.name}")
    except BadgeType.DoesNotExist:
        print(f"✗ ไม่พบ: {color}")

print("\nเสร็จสิ้น!")

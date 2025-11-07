"""Template tags for registry app"""
from django import template

register = template.Library()

# Status choices mapping - ต้องตรงกับ BadgeRequest.STATUS_CHOICES
STATUS_CHOICES = {
    'draft': 'ร่าง',
    'photo_uploaded': 'อัปโหลดรูปแล้ว',
    'ready_to_submit': 'พร้อมส่ง',
    'submitted': 'ส่งแล้ว',
    'under_review': 'กำลังตรวจสอบ',
    'approved': 'อนุมัติ',
    'rejected': 'ส่งกลับ',
    'badge_created': 'สร้างบัตรแล้ว',
    'printed': 'พิมพ์แล้ว',
    'completed': 'เสร็จสิ้น',
}


@register.filter
def status_display(status_code):
    """
    แปลงรหัสสถานะเป็นข้อความภาษาไทย

    Usage: {{ log.new_status|status_display }}
    """
    return STATUS_CHOICES.get(status_code, status_code)

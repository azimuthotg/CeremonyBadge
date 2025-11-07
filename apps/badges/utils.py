"""
Utility functions for badge generation
"""
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


def arabic_to_thai_numerals(number):
    """
    แปลงเลขอารบิกเป็นเลขไทย

    Args:
        number: เลขอารบิก (int หรือ str)

    Returns:
        str: เลขไทย

    Examples:
        >>> arabic_to_thai_numerals(123)
        '๑๒๓'
        >>> arabic_to_thai_numerals('001')
        '๐๐๑'
    """
    thai_digits = ['๐', '๑', '๒', '๓', '๔', '๕', '๖', '๗', '๘', '๙']
    number_str = str(number)
    return ''.join(thai_digits[int(digit)] for digit in number_str)


def get_badge_template_path(badge_type_color):
    """
    ดึง path ของรูปพื้นหลังบัตรตามสี

    Args:
        badge_type_color: สีบัตร (pink, red, yellow, green)

    Returns:
        str: path ของไฟล์รูปพื้นหลัง
    """
    template_map = {
        'pink': 'template_card/pink.png',
        'red': 'template_card/red.png',
        'yellow': 'template_card/yellow.png',
        'green': 'template_card/green.png',
    }

    template_file = template_map.get(badge_type_color)
    if not template_file:
        raise ValueError(f"Invalid badge type color: {badge_type_color}")

    template_path = os.path.join(settings.BASE_DIR, template_file)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")

    return template_path


def generate_badge_image(staff_profile, badge_number, photo=None):
    """
    สร้างรูปบัตรจากข้อมูลบุคลากร

    Args:
        staff_profile: StaffProfile object
        badge_number: หมายเลขบัตร (เลขอารบิก)
        photo: Photo object (optional)

    Returns:
        PIL.Image: รูปบัตรที่สร้างเสร็จ
    """
    # 1. โหลดรูปพื้นหลัง
    badge_type_color = staff_profile.badge_type.color
    template_path = get_badge_template_path(badge_type_color)
    badge_img = Image.open(template_path).convert('RGB')

    # 2. วางรูปบุคลากร (มุมซ้ายบน)
    if photo and photo.cropped_photo:
        try:
            # โหลดรูปที่ crop แล้ว
            photo_path = photo.cropped_photo.path
            staff_photo = Image.open(photo_path).convert('RGB')

            # Resize รูปถ้าจำเป็น (ให้เหมาะกับบัตร)
            # ตอนนี้รูป cropped เป็น 300x400 อยู่แล้ว
            # วางที่มุมซ้ายบน (เผื่อพื้นที่ขอบเล็กน้อย)
            position = (20, 20)  # x=20px, y=20px จากมุมซ้ายบน
            badge_img.paste(staff_photo, position)
        except Exception as e:
            print(f"Error loading staff photo: {e}")

    # 3. วางข้อความ
    draw = ImageDraw.Draw(badge_img)

    # โหลด font THSarabunNew
    try:
        base_dir = settings.BASE_DIR
        font_regular_path = os.path.join(base_dir, 'static', 'fonts', 'THSarabunNew.ttf')
        font_bold_path = os.path.join(base_dir, 'static', 'fonts', 'THSarabunNew Bold.ttf')

        # ใช้ขนาดใหญ่ขึ้นเพื่อให้อ่านง่าย
        font_regular = ImageFont.truetype(font_regular_path, 48)  # ขนาด 48
        font_bold = ImageFont.truetype(font_bold_path, 60)        # ขนาด 60
        font_small = ImageFont.truetype(font_regular_path, 40)    # ขนาด 40 สำหรับข้อความเล็ก

        print(f"Font loaded successfully: {font_regular_path}")
    except Exception as e:
        print(f"Error loading THSarabunNew font: {e}")
        # Fallback to default
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # สีข้อความ (ดำ)
    text_color = (0, 0, 0)

    # ขนาดบัตร: 1122 x 768 px
    badge_width = badge_img.width
    badge_height = badge_img.height

    # 1. หมายเลขบัตร (เลขไทย) - มุมบนขวา
    thai_badge_number = arabic_to_thai_numerals(badge_number.split('-')[1])
    badge_number_text = f"หมายเลข {thai_badge_number}"
    draw.text((badge_width - 350, 30), badge_number_text, fill=text_color, font=font_bold)

    # 2. โซน (ตัวย่อ) - มุมบนขวา (ใต้หมายเลข)
    if staff_profile.zone:
        zone_text = f" {staff_profile.zone.code}"

        # สร้าง font สำหรับโซนขนาด 80 ตัวหนา
        try:
            font_zone = ImageFont.truetype(font_bold_path, 120)
        except:
            font_zone = font_bold

        # วาดกรอบสี่เหลี่ยม
        try:
            bbox = draw.textbbox((0, 0), zone_text, font=font_zone)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = 120
            text_height = 60

        # ตำแหน่งกรอบ (อิสระ)
        box_x = badge_width - 160  # ตำแหน่ง x ของกรอบ
        box_y = 655                 # ตำแหน่ง y ของกรอบ

        # วาดกรอบ (ขยายความยาว/กว้าง แกน X เป็น 150%)
        # ซ้าย-ขวา: -60 ถึง +60 (padding 120px - เพิ่ม 150%)
        # บน-ล่าง: -20 ถึง +30 (ความสูงคงเดิม)
        draw.rectangle(
            [(box_x - 60, box_y - 20), (box_x + text_width + 60, box_y + text_height + 30)],
            outline=(255, 0, 0),
            width=4
        )

        # ตำแหน่งตัวอักษร (อิสระ - ปรับได้เอง)
        text_x = badge_width - 170  # ตำแหน่ง x ของตัวอักษร
        text_y = 620                 # ตำแหน่ง y ของตัวอักษร
        draw.text((text_x, text_y), zone_text, fill=text_color, font=font_zone)

    # 3. ยศ ชื่อ - บรรทัดที่ 1
    first_line = f"{staff_profile.title} {staff_profile.first_name}"
    name_y = badge_height - 330
    draw.text((30, name_y), first_line, fill=text_color, font=font_bold)

    # นามสกุล - บรรทัดที่ 2
    name_y += 60  # ขึ้นบรรทัดใหม่
    draw.text((60, name_y), staff_profile.last_name, fill=text_color, font=font_bold)

    # 4. หน้าที่/ตำแหน่ง - ตำแหน่งอิสระ
    position_text = staff_profile.position
    position_y = badge_height - 280  # กำหนดตำแหน่งเอง
    draw.text((510, position_y), position_text, fill=text_color, font=font_bold)

    # 5. วันที่ปฏิบัติงาน - ล่างสุด (เลขไทย)
    from apps.settings_app.models import SystemSetting
    from apps.registry.utils import format_thai_date

    work_date_setting = SystemSetting.objects.filter(key='work_date').first()

    if work_date_setting:
        work_date = format_thai_date(work_date_setting.value, short=True, use_thai_numerals=True)
        work_date_text = f"วันที่ {work_date}"
        date_y = badge_height - 220
        draw.text((450, date_y), work_date_text, fill=text_color, font=font_bold)

    # 6. ข้อมูลผู้เซ็นบัตร
    # Note: ตอนสร้างบัตรครั้งแรกยังไม่รู้ว่าจะใช้ผู้เซ็นคนไหน
    # จะเพิ่มข้อมูลผู้เซ็นตอนพิมพ์แทน (ดูที่ utils_signature.py)

    return badge_img


def save_badge_image(badge_img, badge_number):
    """
    บันทึกรูปบัตรเป็นไฟล์

    Args:
        badge_img: PIL.Image object
        badge_number: หมายเลขบัตร

    Returns:
        str: relative path ของไฟล์ที่บันทึก
    """
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    badges_dir = os.path.join(settings.MEDIA_ROOT, 'badges', 'generated')
    os.makedirs(badges_dir, exist_ok=True)

    # สร้างชื่อไฟล์
    filename = f'badge_{badge_number}.png'
    filepath = os.path.join(badges_dir, filename)

    # บันทึกรูป
    badge_img.save(filepath, 'PNG', quality=95)

    # Return relative path สำหรับเก็บใน database
    return os.path.join('badges', 'generated', filename)


def get_next_badge_number(badge_type):
    """
    ดึงหมายเลขบัตรถัดไปสำหรับประเภทบัตรนั้นๆ

    Args:
        badge_type: BadgeType object

    Returns:
        str: หมายเลขบัตรในรูปแบบ "ชื่อสี-เลขไทย 3 หลัก" เช่น "pink-๐๐๑"
    """
    from apps.badges.models import Badge

    # นับจำนวนบัตรที่มีอยู่แล้วสำหรับประเภทนี้
    count = Badge.objects.filter(badge_type=badge_type).count()
    next_number = count + 1

    # แปลงเป็นเลขไทย 3 หลัก (เติม 0 ข้างหน้า)
    thai_number = arabic_to_thai_numerals(str(next_number).zfill(3))

    # สร้างหมายเลขบัตร
    badge_number = f"{badge_type.color}-{thai_number}"

    return badge_number

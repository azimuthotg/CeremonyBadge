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

    # 2. วางรูปบุคลากร (มุมซ้ายบน) - เฉพาะบัตรสีชมพูและสีแดง
    if badge_type_color in ['pink', 'red'] and photo and photo.cropped_photo:
        try:
            # โหลดรูปที่ crop แล้ว
            photo_path = photo.cropped_photo.path
            staff_photo = Image.open(photo_path).convert('RGB')

            # Resize รูปให้เล็กลง (จากเดิม 300x400 เหลือ 270x360 = 90%)
            new_width = 270
            new_height = 360
            staff_photo = staff_photo.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # วางที่มุมซ้ายบน - เว้นขอบเล็กน้อย 3px
            position = (3, 3)  # x=3px (เว้นขอบซ้ายนิดหน่อย), y=3px (เว้นขอบบนนิดหน่อย)
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
        font_bold_large = ImageFont.truetype(font_bold_path, 70)  # ขนาด 70 สำหรับตำแหน่งและวันที่
        font_small = ImageFont.truetype(font_regular_path, 40)    # ขนาด 40 สำหรับข้อความเล็ก

        print(f"Font loaded successfully: {font_regular_path}")
    except Exception as e:
        print(f"Error loading THSarabunNew font: {e}")
        # Fallback to default
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_bold_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # สีข้อความ (ดำ)
    text_color = (0, 0, 0)

    # ขนาดบัตร: 1122 x 768 px
    badge_width = badge_img.width
    badge_height = badge_img.height

    # 1. หมายเลขบัตร (เลขไทย) - มุมบนขวา (ขยับขึ้น 5px และชิดขวาอีก 60px)
    thai_badge_number = arabic_to_thai_numerals(badge_number.split('-')[1])
    badge_number_text = f"หมายเลข {thai_badge_number}"
    draw.text((badge_width - 290, 25), badge_number_text, fill=text_color, font=font_bold)

    # 2. โซน (ตัวย่อ) - มุมบนขวา (ใต้หมายเลข) - ไม่มีกรอบ, ตัวอักษรสีแดง, ขนาดใหญ่ขึ้น
    if staff_profile.zone:
        zone_text = f" {staff_profile.zone.code}"

        # สร้าง font สำหรับโซน ขนาด 180
        try:
            font_zone = ImageFont.truetype(font_bold_path, 180)
        except:
            font_zone = font_bold

        # ตำแหน่งตัวอักษร (อิสระ - ปรับได้เอง) - ขยับขึ้นจากมุมล่าง
        # ปรับ X ตามจำนวนตัวอักษร เพื่อให้อยู่ตรงกลาง
        zone_code_length = len(staff_profile.zone.code.strip())
        if zone_code_length == 1:
            text_x = badge_width - 220  # อักษร 1 ตัว เช่น A, B, C
        else:
            text_x = badge_width - 290  # อักษร 2+ ตัว เช่น D, E (ค่าปัจจุบัน)

        text_y = 570                 # ตำแหน่ง y (ขยับขึ้นจาก 620)
        zone_color = (255, 0, 0)     # สีแดง RGB
        draw.text((text_x, text_y), zone_text, fill=zone_color, font=font_zone)

    # 3. ชื่อ 2 บรรทัด (เฉพาะบัตรสีชมพูและสีแดง - บัตรสีเหลืองและสีเขียวไม่ต้องแสดงชื่อ)
    if badge_type_color in ['pink', 'red']:
        # ใช้ display_name ถ้ามี มิฉะนั้นใช้ first_line/last_line
        if staff_profile.display_name:
            # แยกบรรทัดด้วย | (เช่น "ศ. ดร.นายแพทย์กระแส|ชนะวงศ์")
            name_lines = staff_profile.display_name.split('|')

            if len(name_lines) == 2:
                # มี 2 บรรทัด (บรรทัด 1 | บรรทัด 2) - ขยับขึ้น 40px (ปรับลงมา 10px จาก 410)
                name_y = badge_height - 400
                draw.text((30, name_y), name_lines[0].strip(), fill=text_color, font=font_bold)

                # นามสกุล - บรรทัดที่ 2
                name_y += 60
                draw.text((60, name_y), name_lines[1].strip(), fill=text_color, font=font_bold)
            else:
                # แสดงบรรทัดเดียว (ไม่มี |) - ปรับลงมา 10px
                name_y = badge_height - 380
                draw.text((30, name_y), staff_profile.display_name, fill=text_color, font=font_bold)
        else:
            # ใช้ first_line และ last_line
            # บรรทัด 1: ยศชื่อ (ไม่เว้นวรรค) - ขยับขึ้น 40px (ปรับลงมา 10px จาก 410)
            name_y = badge_height - 400
            draw.text((30, name_y), staff_profile.first_line, fill=text_color, font=font_bold)

            # บรรทัด 2: นามสกุล
            name_y += 60  # ขึ้นบรรทัดใหม่
            draw.text((60, name_y), staff_profile.last_line, fill=text_color, font=font_bold)

    # 4. หน้าที่/ตำแหน่ง - ปรับ X ให้อยู่กลางโลโก้ตามความยาวข้อความ
    position_text = f" {staff_profile.position}"  # เพิ่มช่องว่างหน้า
    position_y = badge_height - 290  # กำหนดตำแหน่งเอง

    # กำหนด X ตามข้อความเพื่อให้อยู่กลางโลโก้
    if "ผู้ร่วมพิธี" in staff_profile.position:
        position_x = 480  # ข้อความสั้น
    elif "ผู้ปฏิบัติงาน" in staff_profile.position:
        position_x = 445  # ข้อความยาวกว่า เลื่อนซ้ายนิดหน่อย
    else:
        position_x = 480  # ค่า default (ใช้เท่ากับผู้ร่วมพิธี)

    draw.text((position_x, position_y), position_text, fill=text_color, font=font_bold_large)

    # 5. วันที่ปฏิบัติงาน - ล่างสุด (เลขไทย)
    from apps.settings_app.models import SystemSetting
    from apps.registry.utils import format_thai_date

    work_date_setting = SystemSetting.objects.filter(key='work_date').first()

    if work_date_setting:
        work_date = format_thai_date(work_date_setting.value, short=True, use_thai_numerals=True)
        work_date_text = f" {work_date}"  # เว้นวรรคหน้า 1 เคาะ เช่น " ๒๔ ธ.ค. ๒๕๖๘"
        date_y = badge_height - 230
        draw.text((410, date_y), work_date_text, fill=text_color, font=font_bold_large)

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

    # หาหมายเลขสูงสุดที่มีอยู่แล้วสำหรับประเภทนี้
    # เพื่อป้องกันปัญหาเลขซ้ำเมื่อมีการลบบัตร (เช่น เปลี่ยนสีบัตร)
    badges = Badge.objects.filter(badge_type=badge_type)

    if badges.exists():
        # ดึงหมายเลขทั้งหมดและแปลงจากเลขไทยเป็นเลขอารบิก
        max_number = 0
        for badge in badges:
            # badge_number format: "pink-๐๐๗" → แยกเอาส่วน "๐๐๗"
            number_part = badge.badge_number.split('-')[1]
            # แปลงเลขไทยเป็นเลขอารบิก
            arabic_number = 0
            for digit in number_part:
                arabic_digit = '๐๑๒๓๔๕๖๗๘๙'.index(digit) if digit in '๐๑๒๓๔๕๖๗๘๙' else 0
                arabic_number = arabic_number * 10 + arabic_digit
            max_number = max(max_number, arabic_number)

        next_number = max_number + 1
    else:
        # ถ้ายังไม่มีบัตรเลย เริ่มจาก 1
        next_number = 1

    # แปลงเป็นเลขไทย 3 หลัก (เติม 0 ข้างหน้า)
    thai_number = arabic_to_thai_numerals(str(next_number).zfill(3))

    # สร้างหมายเลขบัตร
    badge_number = f"{badge_type.color}-{thai_number}"

    return badge_number

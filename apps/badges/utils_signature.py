"""
Utility functions for badge signature
"""
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings


def add_signature_to_badge(badge_img, signatory, include_signature_image=True):
    """
    เพิ่มข้อมูลผู้เซ็นบัตร (และลายเซ็นถ้าเป็นอิเล็กทรอนิกส์)

    Args:
        badge_img: PIL.Image object (บัตรที่สร้างแล้ว)
        signatory: BadgeSignatory object
        include_signature_image: True = วางรูปลายเซ็น (อิเล็กทรอนิกส์), False = ไม่วาง (เซ็นมือจริง)

    Returns:
        PIL.Image: บัตรพร้อมข้อมูลผู้เซ็น
    """
    if not signatory:
        return badge_img

    try:
        badge_width = badge_img.width
        badge_height = badge_img.height

        # ตำแหน่งพื้นที่ลายเซ็น (มุมซ้ายล่าง)
        sig_x = 60  # เลื่อนขวา 30 (จาก 30 เป็น 60)
        sig_y = badge_height - 270  # ลงมาอีก 10 (จาก -280 เป็น -270)

        signature_height = 0  # ความสูงของลายเซ็น (จะใช้คำนวณตำแหน่งข้อความ)

        # ถ้าเลือกลายเซ็นอิเล็กทรอนิกส์ → วางรูปลายเซ็น
        if include_signature_image and signatory.signature_image:
            # โหลดลายเซ็น
            sig_path = signatory.signature_image.path
            signature = Image.open(sig_path).convert('RGBA')

            # Resize ลายเซ็นให้เหมาะสม (ขยาย 50% อีกครั้ง จาก 300x120 เป็น 450x180)
            max_width = 450  # เพิ่มจาก 300 (+50%)
            max_height = 180  # เพิ่มจาก 120 (+50%)
            signature.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # แปลง badge เป็น RGBA
            if badge_img.mode != 'RGBA':
                badge_img = badge_img.convert('RGBA')

            # วางลายเซ็น
            badge_img.paste(signature, (sig_x, sig_y), signature)

            # แปลงกลับเป็น RGB
            badge_img = badge_img.convert('RGB')

            signature_height = signature.height
        else:
            # เซ็นมือจริง → ไม่วางรูป แต่เว้นพื้นที่ไว้
            signature_height = 180  # เว้นพื้นที่เท่ากับลายเซ็นอิเล็กทรอนิกส์ใหม่

        # เพิ่มข้อความผู้เซ็น (ทั้งเซ็นมือจริงและอิเล็กทรอนิกส์)
        draw = ImageDraw.Draw(badge_img)

        # โหลด font (ตัวหนา) - ขนาด 50 สำหรับข้อมูลผู้เซ็น
        try:
            base_dir = settings.BASE_DIR
            font_bold_path = os.path.join(base_dir, 'static', 'fonts', 'THSarabunNew Bold.ttf')
            font_text = ImageFont.truetype(font_bold_path, 50)
        except:
            font_text = ImageFont.load_default()

        text_color = (0, 0, 0)

        # ตำแหน่งข้อความ - ชิดซ้ายคงที่ (ไม่ขึ้นกับลายเซ็น)
        text_x = 30  # ชิดซ้าย X=30 คงที่

        # บรรทัดที่ 1: (ยศ + ชื่อ-นามสกุล) - เลื่อนขึ้น 20 (จาก -90 เป็น -110)
        name_text_y = badge_height - 110
        rank_prefix = f"{signatory.rank}" if signatory.rank else ""
        full_name = f"({rank_prefix}{signatory.first_name} {signatory.last_name})"
        draw.text((text_x, name_text_y), full_name, fill=text_color, font=font_text)

        # บรรทัดที่ 2: ตำแหน่ง (ถ้ามี) - เลื่อนขึ้น 20 (จาก -50 เป็น -70)
        if signatory.position:
            position_text_y = badge_height - 70
            position_with_indent = f" {signatory.position}"  # เว้นวรรคหน้า
            draw.text((text_x, position_text_y), position_with_indent, fill=text_color, font=font_text)

        return badge_img

    except Exception as e:
        print(f"Error adding signature info to badge: {e}")
        return badge_img


def regenerate_badge_with_signature(badge, signatory, signature_type='electronic'):
    """
    สร้างบัตรใหม่พร้อมข้อมูลผู้เซ็น (และลายเซ็นถ้าเป็นอิเล็กทรอนิกส์)

    Args:
        badge: Badge object
        signatory: BadgeSignatory object
        signature_type: 'manual' = เซ็นมือจริง (มีชื่อ ไม่มีรูปลายเซ็น),
                        'electronic' = อิเล็กทรอนิกส์ (มีชื่อ + รูปลายเซ็น)

    Returns:
        str: path ของไฟล์บัตรใหม่
    """
    from .utils import generate_badge_image, save_badge_image
    from apps.registry.models import Photo

    try:
        staff_profile = badge.staff_profile
        badge_number = badge.badge_number

        # 1. ดึงรูปภาพ (ถ้ามี)
        photo = None
        if staff_profile.badge_type.requires_photo:
            try:
                photo = Photo.objects.get(staff_profile=staff_profile)
            except Photo.DoesNotExist:
                pass

        # 2. สร้างบัตรใหม่ (ไม่มีลายเซ็น)
        badge_img = generate_badge_image(staff_profile, badge_number, photo)

        # 3. เพิ่มข้อมูลผู้เซ็น
        include_sig_image = (signature_type == 'electronic')  # True = วางรูปลายเซ็น, False = ไม่วาง
        badge_img = add_signature_to_badge(badge_img, signatory, include_signature_image=include_sig_image)

        # 4. บันทึกไฟล์ (ทับไฟล์เดิม)
        badge_file_path = save_badge_image(badge_img, badge_number)

        return badge_file_path

    except Exception as e:
        print(f"Error regenerating badge with signature: {e}")
        raise e

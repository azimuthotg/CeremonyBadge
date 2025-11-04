from django.db import models
from django.conf import settings
import qrcode
import hashlib
import hmac
from io import BytesIO
from django.core.files import File

# Create your models here.

class BadgeType(models.Model):
    """ประเภทบัตร (สีบัตร)"""
    COLOR_CHOICES = [
        ('pink', 'ชมพู - บุคลากรชั้นใน'),
        ('red', 'แดง - บุคลากรชั้นใน'),
        ('yellow', 'เหลือง - บุคลากรชั้นกลาง'),
        ('green', 'เขียว - บุคลากรชั้นนอก'),
    ]

    name = models.CharField(max_length=100, verbose_name="ชื่อประเภท")
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, unique=True, verbose_name="สี")
    color_code = models.CharField(max_length=7, verbose_name="รหัสสี (Hex)", help_text="เช่น #FFC0CB")
    description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'badge_types'
        verbose_name = 'ประเภทบัตร'
        verbose_name_plural = 'ประเภทบัตร'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_color_display()})"

    def requires_photo(self):
        """ตรวจสอบว่าประเภทบัตรนี้ต้องการรูปภาพหรือไม่"""
        # Yellow และ Green ไม่ต้องมีรูป
        return self.color not in ['yellow', 'green']


class BadgeTemplate(models.Model):
    """แม่แบบบัตร"""
    badge_type = models.OneToOneField(
        BadgeType,
        on_delete=models.CASCADE,
        related_name='template',
        verbose_name="ประเภทบัตร"
    )
    template_file = models.FileField(
        upload_to='templates/badges/',
        blank=True,
        null=True,
        verbose_name="ไฟล์แม่แบบ"
    )
    background_color = models.CharField(max_length=7, verbose_name="สีพื้นหลัง")
    text_color = models.CharField(max_length=7, default='#000000', verbose_name="สีข้อความ")
    logo_position_x = models.IntegerField(default=0, verbose_name="ตำแหน่งโลโก้ X")
    logo_position_y = models.IntegerField(default=0, verbose_name="ตำแหน่งโลโก้ Y")
    photo_position_x = models.IntegerField(default=0, verbose_name="ตำแหน่งรูปภาพ X")
    photo_position_y = models.IntegerField(default=0, verbose_name="ตำแหน่งรูปภาพ Y")
    qr_position_x = models.IntegerField(default=0, verbose_name="ตำแหน่ง QR X")
    qr_position_y = models.IntegerField(default=0, verbose_name="ตำแหน่ง QR Y")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'badge_templates'
        verbose_name = 'แม่แบบบัตร'
        verbose_name_plural = 'แม่แบบบัตร'

    def __str__(self):
        return f"แม่แบบ - {self.badge_type.name}"


class Badge(models.Model):
    """บัตรผู้ปฏิบัติงาน"""
    staff_profile = models.OneToOneField(
        'registry.StaffProfile',
        on_delete=models.CASCADE,
        related_name='badge',
        verbose_name="ข้อมูลบุคลากร"
    )
    badge_type = models.ForeignKey(
        BadgeType,
        on_delete=models.PROTECT,
        related_name='badges',
        verbose_name="ประเภทบัตร"
    )
    badge_number = models.CharField(max_length=50, unique=True, verbose_name="หมายเลขบัตร")
    qr_code = models.ImageField(
        upload_to='qrcodes/',
        blank=True,
        null=True,
        verbose_name="QR Code"
    )
    qr_data = models.TextField(verbose_name="ข้อมูล QR")
    qr_signature = models.CharField(max_length=255, verbose_name="ลายเซ็น QR")
    badge_file = models.FileField(
        upload_to='badges/',
        blank=True,
        null=True,
        verbose_name="ไฟล์บัตร"
    )
    is_printed = models.BooleanField(default=False, verbose_name="พิมพ์แล้ว")
    printed_count = models.IntegerField(default=0, verbose_name="จำนวนครั้งที่พิมพ์")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งานได้")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='badges_created',
        verbose_name="ผู้สร้าง"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'badges'
        verbose_name = 'บัตร'
        verbose_name_plural = 'บัตร'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.badge_number} - {self.staff_profile.full_name}"

    def generate_qr_code(self, secret_key='ceremony_badge_2567'):
        """สร้าง QR Code พร้อม HMAC Signature"""
        # สร้างข้อมูล QR
        self.qr_data = f"{self.badge_number}|{self.staff_profile.full_name}|{self.badge_type.name}"

        # สร้าง HMAC Signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            self.qr_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        self.qr_signature = signature

        # สร้าง QR Code Image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr_content = f"{self.qr_data}|{signature}"
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # บันทึกเป็น ImageField
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_{self.badge_number}.png'
        self.qr_code.save(file_name, File(buffer), save=False)
        buffer.close()

        return True

    def verify_qr_signature(self, secret_key='ceremony_badge_2567'):
        """ตรวจสอบความถูกต้องของ QR Code"""
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            self.qr_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.qr_signature, expected_signature)


class PrintLog(models.Model):
    """บันทึกการพิมพ์บัตร"""
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='print_logs',
        verbose_name="บัตร"
    )
    printed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='print_logs',
        verbose_name="ผู้พิมพ์"
    )
    printed_at = models.DateTimeField(auto_now_add=True, verbose_name="พิมพ์เมื่อ")
    printer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="ชื่อเครื่องพิมพ์")
    notes = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    class Meta:
        db_table = 'print_logs'
        verbose_name = 'บันทึกการพิมพ์'
        verbose_name_plural = 'บันทึกการพิมพ์'
        ordering = ['-printed_at']

    def __str__(self):
        return f"พิมพ์: {self.badge.badge_number} - {self.printed_at.strftime('%d/%m/%Y %H:%M')}"

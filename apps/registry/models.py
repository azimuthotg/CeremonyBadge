from django.db import models
from django.conf import settings
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

# Create your models here.

class Zone(models.Model):
    """พื้นที่/โซนปฏิบัติงาน"""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="รหัสโซน",
        help_text="เช่น A, B, C"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="ชื่อโซน",
        help_text="เช่น กอร.ถปภ. ณ ม.นครพนม"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="คำอธิบาย",
        help_text="รายละเอียดเพิ่มเติมเกี่ยวกับโซน"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="ลำดับการแสดงผล",
        help_text="ใช้สำหรับเรียงลำดับการแสดงผล"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="ใช้งาน"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'zones'
        verbose_name = 'โซนปฏิบัติงาน'
        verbose_name_plural = 'โซนปฏิบัติงาน'
        ordering = ['order', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_description(self):
        """คำอธิบายแบบเต็ม"""
        return f"{self.name} ({self.code})"

class StaffProfile(models.Model):
    """ข้อมูลบุคลากรผู้ปฏิบัติงาน"""

    # ข้อมูลพื้นฐาน
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.PROTECT,
        related_name='staff_profiles',
        verbose_name="หน่วยงาน"
    )
    title = models.CharField(
        max_length=50,
        verbose_name="ยศ",
        help_text="เช่น นาย, นาง, น.ส., พล.อ., พล.ต. ฯลฯ"
    )
    first_name = models.CharField(max_length=100, verbose_name="ชื่อ")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล")
    national_id = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        verbose_name="บัตรประชาชน ๑๓ หลัก",
        help_text="เลขบัตรประชาชน 13 หลัก"
    )

    # ข้อมูลการทำงาน
    position = models.CharField(max_length=255, verbose_name="ตำแหน่ง/หน้าที่")
    badge_type = models.ForeignKey(
        'badges.BadgeType',
        on_delete=models.PROTECT,
        related_name='staff_profiles',
        verbose_name="ประเภทบัตร"
    )
    zone = models.ForeignKey(
        Zone,
        on_delete=models.PROTECT,
        related_name='staff_profiles',
        blank=True,
        null=True,
        verbose_name="พื้นที่/โซน",
        help_text="ระบุพื้นที่หรือโซนที่ปฏิบัติงาน"
    )

    # ข้อมูลส่วนตัว
    age = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="อายุ"
    )
    vehicle_registration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="ทะเบียนรถ"
    )

    # ข้อมูลติดต่อ
    email = models.EmailField(blank=True, null=True, verbose_name="อีเมล")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")

    # การรับวัคซีน
    vaccine_dose_1 = models.BooleanField(default=False, verbose_name="วัคซีนเข็ม ๑")
    vaccine_dose_2 = models.BooleanField(default=False, verbose_name="วัคซีนเข็ม ๒")
    vaccine_dose_3 = models.BooleanField(default=False, verbose_name="วัคซีนเข็ม ๓")
    vaccine_dose_4 = models.BooleanField(default=False, verbose_name="วัคซีนเข็ม ๔")

    # การตรวจโควิดก่อนการปฏิบัติงาน
    test_rt_pcr = models.BooleanField(default=False, verbose_name="RT-PCR")
    test_atk = models.BooleanField(default=False, verbose_name="ATK")
    test_temperature = models.BooleanField(default=False, verbose_name="วัดอุณหภูมิ")

    # หมายเหตุและข้อมูลระบบ
    notes = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='staff_profiles_created',
        verbose_name="ผู้สร้าง"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'staff_profiles'
        verbose_name = 'ข้อมูลบุคลากร'
        verbose_name_plural = 'ข้อมูลบุคลากร'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """ชื่อเต็ม"""
        return f"{self.title}{self.first_name} {self.last_name}"

    @property
    def full_name_with_position(self):
        """ชื่อเต็มพร้อมตำแหน่ง"""
        return f"{self.full_name}\n{self.position}"


class Photo(models.Model):
    """รูปภาพบุคลากร (หลังจาก crop แล้ว)"""
    staff_profile = models.OneToOneField(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='photo',
        verbose_name="ข้อมูลบุคลากร"
    )
    original_photo = models.ImageField(
        upload_to='photos/original/',
        verbose_name="รูปภาพต้นฉบับ"
    )
    cropped_photo = models.ImageField(
        upload_to='photos/cropped/',
        blank=True,
        null=True,
        verbose_name="รูปภาพที่ Crop แล้ว"
    )
    crop_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name="ข้อมูล Crop",
        help_text="เก็บข้อมูลจาก Cropper.js (x, y, width, height, rotate)"
    )
    file_size = models.IntegerField(default=0, verbose_name="ขนาดไฟล์ (bytes)")
    width = models.IntegerField(default=0, verbose_name="ความกว้าง (px)")
    height = models.IntegerField(default=0, verbose_name="ความสูง (px)")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='photos_uploaded',
        verbose_name="ผู้อัปโหลด"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="อัปโหลดเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'photos'
        verbose_name = 'รูปภาพ'
        verbose_name_plural = 'รูปภาพ'

    def __str__(self):
        return f"รูปภาพ - {self.staff_profile.full_name}"


class BadgeRequest(models.Model):
    """คำขอออกบัตร"""
    STATUS_CHOICES = [
        ('draft', 'ร่าง'),
        ('photo_uploaded', 'อัปโหลดรูปแล้ว'),
        ('ready_to_submit', 'พร้อมส่ง'),
        ('submitted', 'ส่งแล้ว'),
        ('under_review', 'กำลังตรวจสอบ'),
        ('approved', 'อนุมัติ'),
        ('rejected', 'ส่งกลับ'),
        ('badge_created', 'สร้างบัตรแล้ว'),
        ('printed', 'พิมพ์แล้ว'),
        ('completed', 'เสร็จสิ้น'),
    ]

    staff_profile = models.OneToOneField(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='badge_request',
        verbose_name="ข้อมูลบุคลากร"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="สถานะ"
    )
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name="ส่งเมื่อ")
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="ตรวจสอบเมื่อ")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badge_requests_reviewed',
        verbose_name="ผู้ตรวจสอบ"
    )
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="อนุมัติเมื่อ")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='badge_requests_approved',
        verbose_name="ผู้อนุมัติ"
    )
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="เหตุผลที่ส่งกลับ")
    notes = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='badge_requests_created',
        verbose_name="ผู้สร้าง"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'badge_requests'
        verbose_name = 'คำขอออกบัตร'
        verbose_name_plural = 'คำขอออกบัตร'
        ordering = ['-created_at']

    def __str__(self):
        return f"คำขอ - {self.staff_profile.full_name} ({self.get_status_display()})"

    def can_edit(self):
        """ตรวจสอบว่าสามารถแก้ไขได้หรือไม่"""
        return self.status in ['draft', 'photo_uploaded', 'ready_to_submit', 'rejected']

    def can_submit(self):
        """ตรวจสอบว่าสามารถส่งได้หรือไม่"""
        # ถ้าต้องการรูป ต้องมีรูปก่อนส่งได้
        if self.staff_profile.badge_type.requires_photo():
            return self.status in ['ready_to_submit', 'rejected'] and hasattr(self.staff_profile, 'photo')
        # ถ้าไม่ต้องการรูป (yellow/green) ส่งได้เลย
        return self.status in ['ready_to_submit', 'rejected']

    def can_approve(self):
        """ตรวจสอบว่าสามารถอนุมัติได้หรือไม่"""
        return self.status in ['submitted', 'under_review']

    def can_reject(self):
        """ตรวจสอบว่าสามารถส่งกลับได้หรือไม่"""
        return self.status in ['submitted', 'under_review']

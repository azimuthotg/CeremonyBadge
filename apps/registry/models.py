from django.db import models
from django.conf import settings
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

# Create your models here.

class StaffProfile(models.Model):
    """ข้อมูลบุคลากรผู้ปฏิบัติงาน"""
    TITLE_CHOICES = [
        ('mr', 'นาย'),
        ('mrs', 'นาง'),
        ('miss', 'นางสาว'),
        ('prof', 'ศาสตราจารย์'),
        ('assoc_prof', 'รองศาสตราจารย์'),
        ('asst_prof', 'ผู้ช่วยศาสตราจารย์'),
        ('dr', 'ดร.'),
    ]

    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.PROTECT,
        related_name='staff_profiles',
        verbose_name="หน่วยงาน"
    )
    title = models.CharField(
        max_length=20,
        choices=TITLE_CHOICES,
        verbose_name="คำนำหน้า"
    )
    first_name = models.CharField(max_length=100, verbose_name="ชื่อ")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล")
    position = models.CharField(max_length=255, verbose_name="ตำแหน่ง")
    email = models.EmailField(blank=True, null=True, verbose_name="อีเมล")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    badge_type = models.ForeignKey(
        'badges.BadgeType',
        on_delete=models.PROTECT,
        related_name='staff_profiles',
        verbose_name="ประเภทบัตร"
    )
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
        return f"{self.get_title_display()}{self.first_name} {self.last_name}"

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
    cropped_photo = ProcessedImageField(
        upload_to='photos/cropped/',
        processors=[ResizeToFill(300, 400)],
        format='JPEG',
        options={'quality': 95},
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
        return self.status in ['ready_to_submit', 'rejected'] and hasattr(self.staff_profile, 'photo')

    def can_approve(self):
        """ตรวจสอบว่าสามารถอนุมัติได้หรือไม่"""
        return self.status in ['submitted', 'under_review']

    def can_reject(self):
        """ตรวจสอบว่าสามารถส่งกลับได้หรือไม่"""
        return self.status in ['submitted', 'under_review']

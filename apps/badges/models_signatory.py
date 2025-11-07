"""
Badge Signatory Model
ผู้มีอำนาจเซ็นบัตร
"""
from django.db import models


class BadgeSignatory(models.Model):
    """ผู้มีอำนาจเซ็นบัตร"""

    rank = models.CharField(max_length=100, blank=True, null=True, verbose_name="ยศ/คำนำหน้า")
    first_name = models.CharField(max_length=100, verbose_name="ชื่อ")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล")
    department = models.CharField(max_length=255, verbose_name="หน่วยงาน")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="ตำแหน่ง")
    signature_image = models.ImageField(
        upload_to='signatures/',
        verbose_name="ลายเซ็นต์อิเล็กทรอนิกส์",
        help_text="ไฟล์ PNG โปร่งใส ขนาดแนะนำ 400x150 px"
    )
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'badge_signatories'
        verbose_name = 'ผู้เซ็นบัตร'
        verbose_name_plural = 'ผู้เซ็นบัตร'
        ordering = ['rank', 'first_name']

    def __str__(self):
        rank_str = f"{self.rank} " if self.rank else ""
        return f"{rank_str}{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """ชื่อ-นามสกุลเต็ม"""
        rank_str = f"{self.rank} " if self.rank else ""
        return f"{rank_str}{self.first_name} {self.last_name}"

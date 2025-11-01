from django.db import models
from django.utils import timezone

# Create your models here.

class ReportCache(models.Model):
    """แคชข้อมูลรายงานและสถิติ - ใช้สำหรับ Dashboard"""
    REPORT_TYPE_CHOICES = [
        ('dashboard_summary', 'สรุป Dashboard'),
        ('department_summary', 'สรุปตามหน่วยงาน'),
        ('badge_type_summary', 'สรุปตามประเภทบัตร'),
        ('status_summary', 'สรุปตามสถานะ'),
        ('daily_summary', 'สรุปรายวัน'),
    ]

    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="ประเภทรายงาน"
    )
    report_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Key รายงาน",
        help_text="เช่น department_id, badge_type_id, date"
    )
    data = models.JSONField(verbose_name="ข้อมูลรายงาน")
    generated_at = models.DateTimeField(auto_now=True, verbose_name="สร้างเมื่อ")
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="หมดอายุเมื่อ",
        help_text="ถ้าไม่ระบุจะไม่หมดอายุ"
    )

    class Meta:
        db_table = 'report_caches'
        verbose_name = 'แคชรายงาน'
        verbose_name_plural = 'แคชรายงาน'
        ordering = ['-generated_at']
        unique_together = [['report_type', 'report_key']]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_key or 'ทั้งหมด'}"

    def is_expired(self):
        """ตรวจสอบว่าแคชหมดอายุหรือไม่"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @classmethod
    def get_or_generate(cls, report_type, report_key=None, generator_func=None, expires_in_hours=1):
        """
        ดึงข้อมูลจากแคชหรือสร้างใหม่ถ้าหมดอายุ

        Args:
            report_type: ประเภทรายงาน
            report_key: Key รายงาน (optional)
            generator_func: ฟังก์ชันสร้างข้อมูลใหม่ (ถ้าแคชหมดอายุ)
            expires_in_hours: จำนวนชั่วโมงก่อนหมดอายุ

        Returns:
            ข้อมูลรายงาน (dict)
        """
        try:
            cache = cls.objects.get(report_type=report_type, report_key=report_key)
            if not cache.is_expired():
                return cache.data
        except cls.DoesNotExist:
            pass

        # สร้างข้อมูลใหม่
        if generator_func:
            data = generator_func()
            expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)

            cache, created = cls.objects.update_or_create(
                report_type=report_type,
                report_key=report_key,
                defaults={
                    'data': data,
                    'expires_at': expires_at
                }
            )
            return cache.data

        return {}

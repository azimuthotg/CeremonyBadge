from django.db import models
from django.conf import settings

# Create your models here.

class ApprovalLog(models.Model):
    """บันทึกประวัติการตรวจสอบและอนุมัติ"""
    ACTION_CHOICES = [
        ('submit', 'ส่งข้อมูล'),
        ('review', 'ตรวจสอบ'),
        ('approve', 'อนุมัติ'),
        ('reject', 'ส่งกลับ'),
        ('edit', 'แก้ไข'),
        ('comment', 'แสดงความคิดเห็น'),
    ]

    badge_request = models.ForeignKey(
        'registry.BadgeRequest',
        on_delete=models.CASCADE,
        related_name='approval_logs',
        verbose_name="คำขอออกบัตร"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="การกระทำ"
    )
    previous_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="สถานะเดิม"
    )
    new_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="สถานะใหม่"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="ความคิดเห็น/หมายเหตุ")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_logs',
        verbose_name="ผู้ดำเนินการ"
    )
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name="ดำเนินการเมื่อ")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")

    class Meta:
        db_table = 'approval_logs'
        verbose_name = 'บันทึกการอนุมัติ'
        verbose_name_plural = 'บันทึกการอนุมัติ'
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.badge_request.staff_profile.full_name} ({self.performed_at.strftime('%d/%m/%Y %H:%M')})"

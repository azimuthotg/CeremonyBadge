from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Department(models.Model):
    """หน่วยงาน/สังกัด"""
    name = models.CharField(max_length=255, verbose_name="ชื่อหน่วยงาน")
    code = models.CharField(max_length=50, unique=True, verbose_name="รหัสหน่วยงาน")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียด")
    order = models.IntegerField(default=0, verbose_name="ลำดับการแสดงผล")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'departments'
        verbose_name = 'หน่วยงาน'
        verbose_name_plural = 'หน่วยงาน'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """ผู้ใช้งานระบบ - ขยายจาก Django User"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('officer', 'Officer'),
        ('submitter', 'Submitter'),
    ]

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="หน่วยงาน"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='submitter',
        verbose_name="บทบาท"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name="ตำแหน่ง")
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")

    class Meta:
        db_table = 'users'
        verbose_name = 'ผู้ใช้งาน'
        verbose_name_plural = 'ผู้ใช้งาน'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == 'admin'

    def is_officer(self):
        return self.role == 'officer'

    def is_submitter(self):
        return self.role == 'submitter'

    def can_manage_all(self):
        """ตรวจสอบว่าสามารถจัดการข้อมูลทั้งหมดได้หรือไม่"""
        return self.role in ['admin', 'officer']

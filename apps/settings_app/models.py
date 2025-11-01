from django.db import models

# Create your models here.

class SystemSetting(models.Model):
    """การตั้งค่าระบบ - แก้ไขได้เฉพาะ Admin"""
    SETTING_TYPE_CHOICES = [
        ('string', 'ข้อความ'),
        ('integer', 'ตัวเลข'),
        ('boolean', 'True/False'),
        ('json', 'JSON'),
        ('file', 'ไฟล์'),
        ('color', 'สี'),
    ]

    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Key",
        help_text="ชื่อตัวตั้งค่า เช่น qr_secret_key, logo_file, primary_color"
    )
    value = models.TextField(verbose_name="ค่า")
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPE_CHOICES,
        default='string',
        verbose_name="ประเภท"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="คำอธิบาย"
    )
    is_active = models.BooleanField(default=True, verbose_name="ใช้งาน")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขล่าสุด")

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'การตั้งค่าระบบ'
        verbose_name_plural = 'การตั้งค่าระบบ'
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value[:50]}"

    @classmethod
    def get_value(cls, key, default=None):
        """ดึงค่าการตั้งค่า"""
        try:
            setting = cls.objects.get(key=key, is_active=True)

            # แปลงค่าตามประเภท
            if setting.setting_type == 'integer':
                return int(setting.value)
            elif setting.setting_type == 'boolean':
                return setting.value.lower() in ['true', '1', 'yes']
            elif setting.setting_type == 'json':
                import json
                return json.loads(setting.value)
            else:
                return setting.value
        except cls.DoesNotExist:
            return default
        except (ValueError, json.JSONDecodeError):
            return default

    @classmethod
    def set_value(cls, key, value, setting_type='string', description=None):
        """ตั้งค่าการตั้งค่า"""
        import json

        # แปลงค่าเป็น string
        if setting_type == 'json':
            value_str = json.dumps(value, ensure_ascii=False)
        elif setting_type == 'boolean':
            value_str = 'true' if value else 'false'
        else:
            value_str = str(value)

        setting, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value_str,
                'setting_type': setting_type,
                'description': description or f'การตั้งค่า {key}'
            }
        )
        return setting

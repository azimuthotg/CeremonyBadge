from django.contrib import admin
from .models import SystemSetting

# Register your models here.

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'setting_type', 'is_active', 'updated_at']
    list_filter = ['setting_type', 'is_active', 'updated_at']
    search_fields = ['key', 'value', 'description']
    ordering = ['key']
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('การตั้งค่า', {
            'fields': ('key', 'value', 'setting_type')
        }),
        ('คำอธิบาย', {
            'fields': ('description', 'is_active')
        }),
    )

    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'ค่า'

    def has_delete_permission(self, request, obj=None):
        if obj and obj.key in ['qr_secret_key', 'primary_color']:
            return False
        return super().has_delete_permission(request, obj)

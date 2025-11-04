from django.contrib import admin
from .models import BadgeType, BadgeTemplate, Badge, PrintLog

# Register your models here.

@admin.register(BadgeType)
class BadgeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'color_code', 'description', 'is_active', 'created_at']
    list_filter = ['color', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    date_hierarchy = 'created_at'
    list_editable = ['is_active']

    fieldsets = (
        ('ข้อมูลประเภทบัตร', {
            'fields': ('name', 'color', 'color_code', 'description')
        }),
        ('การแสดงผล', {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BadgeTemplate)
class BadgeTemplateAdmin(admin.ModelAdmin):
    list_display = ['badge_type', 'background_color', 'text_color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['badge_type__name']
    ordering = ['badge_type']
    date_hierarchy = 'created_at'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['badge_number', 'staff_profile', 'badge_type', 'is_printed', 'printed_count', 'is_active', 'created_at']
    list_filter = ['badge_type', 'is_printed', 'is_active', 'created_at']
    search_fields = ['badge_number', 'staff_profile__first_name', 'staff_profile__last_name', 'qr_data']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['qr_code', 'qr_data', 'qr_signature', 'badge_file']


@admin.register(PrintLog)
class PrintLogAdmin(admin.ModelAdmin):
    list_display = ['badge', 'printed_by', 'printed_at', 'printer_name']
    list_filter = ['printed_at', 'printer_name']
    search_fields = ['badge__badge_number', 'printed_by__username', 'notes']
    ordering = ['-printed_at']
    date_hierarchy = 'printed_at'
    readonly_fields = ['printed_at']

from django.contrib import admin
from .models import StaffProfile, Photo, BadgeRequest, Zone

# Register your models here.

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['order', 'code']
    list_editable = ['order', 'is_active']

    fieldsets = (
        ('ข้อมูลโซน', {
            'fields': ('code', 'name', 'description')
        }),
        ('การแสดงผล', {
            'fields': ('order', 'is_active')
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'department', 'position', 'badge_type', 'email', 'phone', 'created_at']
    list_filter = ['department', 'badge_type', 'created_at']
    search_fields = ['first_line', 'last_line', 'email', 'phone', 'position']
    ordering = ['last_line', 'first_line']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('ข้อมูลส่วนตัว', {
            'fields': ('first_line', 'last_line')
        }),
        ('ข้อมูลการติดต่อ', {
            'fields': ('email', 'phone')
        }),
        ('ข้อมูลหน่วยงาน', {
            'fields': ('department', 'position', 'badge_type')
        }),
        ('หมายเหตุ', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_by', 'created_at', 'updated_at']


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['staff_profile', 'file_size', 'width', 'height', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['staff_profile__first_line', 'staff_profile__last_line']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['original_photo', 'cropped_photo', 'file_size', 'width', 'height', 'uploaded_by', 'uploaded_at']


@admin.register(BadgeRequest)
class BadgeRequestAdmin(admin.ModelAdmin):
    list_display = ['staff_profile', 'status', 'submitted_at', 'reviewed_by', 'approved_by', 'created_at']
    list_filter = ['status', 'submitted_at', 'reviewed_at', 'approved_at', 'created_at']
    search_fields = ['staff_profile__first_line', 'staff_profile__last_line', 'rejection_reason', 'notes']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('ข้อมูลคำขอ', {
            'fields': ('staff_profile', 'status')
        }),
        ('การตรวจสอบ', {
            'fields': ('submitted_at', 'reviewed_at', 'reviewed_by', 'rejection_reason')
        }),
        ('การอนุมัติ', {
            'fields': ('approved_at', 'approved_by')
        }),
        ('หมายเหตุ', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['submitted_at', 'reviewed_at', 'approved_at', 'created_by', 'created_at', 'updated_at']

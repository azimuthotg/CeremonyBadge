from django.contrib import admin
from .models import StaffProfile, Photo, BadgeRequest

# Register your models here.

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'department', 'position', 'badge_type', 'email', 'phone', 'created_at']
    list_filter = ['department', 'badge_type', 'title', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'position']
    ordering = ['last_name', 'first_name']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('ข้อมูลส่วนตัว', {
            'fields': ('title', 'first_name', 'last_name')
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
    search_fields = ['staff_profile__first_name', 'staff_profile__last_name']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['original_photo', 'cropped_photo', 'file_size', 'width', 'height', 'uploaded_by', 'uploaded_at']


@admin.register(BadgeRequest)
class BadgeRequestAdmin(admin.ModelAdmin):
    list_display = ['staff_profile', 'status', 'submitted_at', 'reviewed_by', 'approved_by', 'created_at']
    list_filter = ['status', 'submitted_at', 'reviewed_at', 'approved_at', 'created_at']
    search_fields = ['staff_profile__first_name', 'staff_profile__last_name', 'rejection_reason', 'notes']
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

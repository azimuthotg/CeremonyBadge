from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Department, User

# Register your models here.

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['name']
    date_hierarchy = 'created_at'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'department', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('ข้อมูลเพิ่มเติม', {
            'fields': ('department', 'role', 'phone', 'position')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('ข้อมูลเพิ่มเติม', {
            'fields': ('department', 'role', 'phone', 'position')
        }),
    )

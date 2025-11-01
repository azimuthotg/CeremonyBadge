from django.contrib import admin
from .models import ReportCache

# Register your models here.

@admin.register(ReportCache)
class ReportCacheAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'report_key', 'generated_at', 'expires_at']
    list_filter = ['report_type', 'generated_at', 'expires_at']
    search_fields = ['report_type', 'report_key']
    ordering = ['-generated_at']
    date_hierarchy = 'generated_at'
    readonly_fields = ['report_type', 'report_key', 'data', 'generated_at', 'expires_at']

    def has_add_permission(self, request):
        return False

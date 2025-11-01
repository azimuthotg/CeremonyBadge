from django.contrib import admin
from .models import ApprovalLog

# Register your models here.

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['badge_request', 'action', 'previous_status', 'new_status', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['badge_request__staff_profile__first_name', 'badge_request__staff_profile__last_name', 'comment', 'performed_by__username']
    ordering = ['-performed_at']
    date_hierarchy = 'performed_at'
    readonly_fields = ['badge_request', 'action', 'previous_status', 'new_status', 'performed_by', 'performed_at', 'ip_address']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

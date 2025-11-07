"""Context processors for approvals app"""
from apps.registry.models import BadgeRequest


def approval_counts(request):
    """Add approval counts to template context"""
    if not request.user.is_authenticated:
        return {
            'pending_count': 0,
            'approved_count': 0,
            'rejected_count': 0,
        }

    # Only show counts for officers and admins
    if not request.user.can_manage_all():
        return {
            'pending_count': 0,
            'approved_count': 0,
            'rejected_count': 0,
        }

    pending_count = BadgeRequest.objects.filter(status='submitted').count()
    approved_count = BadgeRequest.objects.filter(status='approved').count()
    rejected_count = BadgeRequest.objects.filter(status='rejected').count()

    return {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }

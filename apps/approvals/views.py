from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from functools import wraps

from apps.registry.models import BadgeRequest, StaffProfile, Photo
from .models import ApprovalLog


# Decorator for officer/admin only views
def officer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['officer', 'admin']:
            messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_client_ip(request):
    """ดึง IP address ของ client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@officer_required
def pending_list(request):
    """หน้ารอตรวจสอบ - รายการที่ส่งมาแล้ว"""
    # Get pending requests (status = submitted)
    requests = BadgeRequest.objects.filter(
        status='submitted'
    ).select_related(
        'staff_profile__department',
        'staff_profile__badge_type',
        'staff_profile__zone',
        'created_by'
    ).order_by('submitted_at')

    # Search
    search = request.GET.get('search', '')
    if search:
        requests = requests.filter(
            Q(staff_profile__first_name__icontains=search) |
            Q(staff_profile__last_name__icontains=search) |
            Q(staff_profile__position__icontains=search)
        )

    # Filter by department
    department_id = request.GET.get('department')
    if department_id:
        requests = requests.filter(staff_profile__department_id=department_id)

    # Filter by badge type
    badge_type_id = request.GET.get('badge_type')
    if badge_type_id:
        requests = requests.filter(staff_profile__badge_type_id=badge_type_id)

    # Filter by zone
    zone_id = request.GET.get('zone')
    if zone_id:
        requests = requests.filter(staff_profile__zone_id=zone_id)

    # Get filter options
    from apps.accounts.models import Department
    from apps.badges.models import BadgeType
    from apps.registry.models import Zone

    departments = Department.objects.filter(is_active=True).order_by('name')
    badge_types = BadgeType.objects.filter(is_active=True).order_by('name')
    zones = Zone.objects.filter(is_active=True).order_by('code')

    context = {
        'requests': requests,
        'search': search,
        'departments': departments,
        'badge_types': badge_types,
        'zones': zones,
        'selected_department': department_id,
        'selected_badge_type': badge_type_id,
        'selected_zone': zone_id,
    }

    return render(request, 'approvals/pending_list.html', context)


@login_required
@officer_required
def review_detail(request, request_id):
    """หน้าตรวจสอบรายละเอียด"""
    badge_request = get_object_or_404(
        BadgeRequest.objects.select_related(
            'staff_profile__department',
            'staff_profile__badge_type',
            'staff_profile__zone',
            'created_by',
            'reviewed_by',
            'approved_by'
        ),
        pk=request_id
    )

    # Get photo
    try:
        photo = Photo.objects.get(staff_profile=badge_request.staff_profile)
    except Photo.DoesNotExist:
        photo = None

    # Get approval logs
    approval_logs = ApprovalLog.objects.filter(
        badge_request=badge_request
    ).select_related('performed_by').order_by('-performed_at')

    context = {
        'badge_request': badge_request,
        'staff_profile': badge_request.staff_profile,
        'photo': photo,
        'approval_logs': approval_logs,
    }

    return render(request, 'approvals/review_detail.html', context)


@login_required
@officer_required
def approve_request(request, request_id):
    """อนุมัติคำขอ"""
    if request.method != 'POST':
        return redirect('approvals:review_detail', request_id=request_id)

    badge_request = get_object_or_404(BadgeRequest, pk=request_id)

    # Check if can approve
    if badge_request.status not in ['submitted', 'under_review']:
        messages.error(request, 'ไม่สามารถอนุมัติคำขอนี้ได้ในสถานะปัจจุบัน')
        return redirect('approvals:review_detail', request_id=request_id)

    # Save previous status
    previous_status = badge_request.status

    # Update status
    from django.utils import timezone
    badge_request.status = 'approved'
    badge_request.approved_by = request.user
    badge_request.approved_at = timezone.now()
    badge_request.save()

    # Create approval log
    ApprovalLog.objects.create(
        badge_request=badge_request,
        action='approve',
        previous_status=previous_status,
        new_status='approved',
        comment=request.POST.get('comment', ''),
        performed_by=request.user,
        ip_address=get_client_ip(request)
    )

    messages.success(request, f'อนุมัติคำขอของ {badge_request.staff_profile.full_name} เรียบร้อยแล้ว')
    return redirect('approvals:pending_list')


@login_required
@officer_required
def reject_request(request, request_id):
    """ส่งกลับแก้ไข"""
    if request.method != 'POST':
        return redirect('approvals:review_detail', request_id=request_id)

    badge_request = get_object_or_404(BadgeRequest, pk=request_id)

    # Check if can reject
    if badge_request.status not in ['submitted', 'under_review']:
        messages.error(request, 'ไม่สามารถส่งกลับคำขอนี้ได้ในสถานะปัจจุบัน')
        return redirect('approvals:review_detail', request_id=request_id)

    # Get rejection reason
    rejection_reason = request.POST.get('rejection_reason', '').strip()
    if not rejection_reason:
        messages.error(request, 'กรุณาระบุเหตุผลในการส่งกลับ')
        return redirect('approvals:review_detail', request_id=request_id)

    # Save previous status
    previous_status = badge_request.status

    # Update status
    badge_request.status = 'rejected'
    badge_request.rejection_reason = rejection_reason
    badge_request.reviewed_by = request.user
    badge_request.save()

    # Create approval log
    ApprovalLog.objects.create(
        badge_request=badge_request,
        action='reject',
        previous_status=previous_status,
        new_status='rejected',
        comment=rejection_reason,
        performed_by=request.user,
        ip_address=get_client_ip(request)
    )

    messages.success(request, f'ส่งกลับคำขอของ {badge_request.staff_profile.full_name} เรียบร้อยแล้ว')
    return redirect('approvals:pending_list')


@login_required
@officer_required
def approved_list(request):
    """หน้ารายการที่อนุมัติแล้ว"""
    requests = BadgeRequest.objects.filter(
        status='approved'
    ).select_related(
        'staff_profile__department',
        'staff_profile__badge_type',
        'staff_profile__zone',
        'approved_by'
    ).order_by('-approved_at')

    # Search and filters (same as pending_list)
    search = request.GET.get('search', '')
    if search:
        requests = requests.filter(
            Q(staff_profile__first_name__icontains=search) |
            Q(staff_profile__last_name__icontains=search) |
            Q(staff_profile__position__icontains=search)
        )

    context = {
        'requests': requests,
        'search': search,
    }

    return render(request, 'approvals/approved_list.html', context)


@login_required
@officer_required
def rejected_list(request):
    """หน้ารายการที่ส่งกลับแก้ไข"""
    requests = BadgeRequest.objects.filter(
        status='rejected'
    ).select_related(
        'staff_profile__department',
        'staff_profile__badge_type',
        'staff_profile__zone',
        'reviewed_by'
    ).order_by('-reviewed_at')

    # Search
    search = request.GET.get('search', '')
    if search:
        requests = requests.filter(
            Q(staff_profile__first_name__icontains=search) |
            Q(staff_profile__last_name__icontains=search) |
            Q(staff_profile__position__icontains=search)
        )

    context = {
        'requests': requests,
        'search': search,
    }

    return render(request, 'approvals/rejected_list.html', context)


@login_required
@officer_required
def bulk_approve(request):
    """อนุมัติหลายรายการพร้อมกัน"""
    if request.method != 'POST':
        return redirect('approvals:pending_list')

    request_ids = request.POST.getlist('request_ids')
    if not request_ids:
        messages.error(request, 'กรุณาเลือกรายการที่ต้องการอนุมัติ')
        return redirect('approvals:pending_list')

    success_count = 0
    error_count = 0

    for request_id in request_ids:
        try:
            badge_request = BadgeRequest.objects.get(pk=request_id)

            # Check if can approve
            if badge_request.status not in ['submitted', 'under_review']:
                error_count += 1
                continue

            # Save previous status
            previous_status = badge_request.status

            # Update status
            badge_request.status = 'approved'
            badge_request.approved_by = request.user
            badge_request.save()

            # Create approval log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='approve',
                previous_status=previous_status,
                new_status='approved',
                comment='อนุมัติเป็นกลุ่ม',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )

            success_count += 1

        except BadgeRequest.DoesNotExist:
            error_count += 1

    if success_count > 0:
        messages.success(request, f'อนุมัติสำเร็จ {success_count} รายการ')
    if error_count > 0:
        messages.warning(request, f'ไม่สามารถอนุมัติได้ {error_count} รายการ')

    return redirect('approvals:pending_list')


@login_required
@officer_required
def bulk_reject(request):
    """ส่งกลับหลายรายการพร้อมกัน"""
    if request.method != 'POST':
        return redirect('approvals:pending_list')

    request_ids = request.POST.getlist('request_ids')
    rejection_reason = request.POST.get('rejection_reason', '').strip()

    if not request_ids:
        messages.error(request, 'กรุณาเลือกรายการที่ต้องการส่งกลับ')
        return redirect('approvals:pending_list')

    if not rejection_reason:
        messages.error(request, 'กรุณาระบุเหตุผลในการส่งกลับ')
        return redirect('approvals:pending_list')

    success_count = 0
    error_count = 0

    for request_id in request_ids:
        try:
            badge_request = BadgeRequest.objects.get(pk=request_id)

            # Check if can reject
            if badge_request.status not in ['submitted', 'under_review']:
                error_count += 1
                continue

            # Save previous status
            previous_status = badge_request.status

            # Update status
            badge_request.status = 'rejected'
            badge_request.rejection_reason = rejection_reason
            badge_request.reviewed_by = request.user
            badge_request.save()

            # Create approval log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='reject',
                previous_status=previous_status,
                new_status='rejected',
                comment=rejection_reason,
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )

            success_count += 1

        except BadgeRequest.DoesNotExist:
            error_count += 1

    if success_count > 0:
        messages.success(request, f'ส่งกลับสำเร็จ {success_count} รายการ')
    if error_count > 0:
        messages.warning(request, f'ไม่สามารถส่งกลับได้ {error_count} รายการ')

    return redirect('approvals:pending_list')


@login_required
@officer_required
def approval_history(request):
    """หน้าประวัติการอนุมัติ"""
    logs = ApprovalLog.objects.select_related(
        'badge_request__staff_profile__department',
        'badge_request__staff_profile__badge_type',
        'performed_by'
    ).order_by('-performed_at')

    # Filter by action
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)

    # Search
    search = request.GET.get('search', '')
    if search:
        logs = logs.filter(
            Q(badge_request__staff_profile__first_name__icontains=search) |
            Q(badge_request__staff_profile__last_name__icontains=search) |
            Q(performed_by__first_name__icontains=search) |
            Q(performed_by__last_name__icontains=search)
        )

    # Pagination - limit to 50 per page
    logs = logs[:50]

    context = {
        'logs': logs,
        'search': search,
        'selected_action': action,
        'action_choices': ApprovalLog.ACTION_CHOICES,
    }

    return render(request, 'approvals/history.html', context)


@login_required
@officer_required
def edit_approved(request, request_id):
    """แก้ไขข้อมูลที่อนุมัติแล้ว (Officer/Admin เท่านั้น)"""
    badge_request = get_object_or_404(BadgeRequest, pk=request_id)
    staff_profile = badge_request.staff_profile

    # ตรวจสอบว่าอนุมัติแล้วหรือยัง
    if badge_request.status not in ['approved', 'badge_created', 'printed', 'completed']:
        messages.error(request, 'สามารถแก้ไขได้เฉพาะรายการที่อนุมัติแล้วเท่านั้น')
        return redirect('approvals:approved_list')

    # เก็บสถานะว่ามีบัตรแล้วหรือยัง
    has_badge = hasattr(staff_profile, 'badge')
    old_badge_number = staff_profile.badge.badge_number if has_badge else None

    # เก็บค่าลงใน session เพื่อให้ wizard รู้ว่าต้อง redirect กลับมาที่ approved_list
    request.session['edit_from_approved'] = True
    request.session['edit_request_id'] = request_id
    request.session['has_badge'] = has_badge
    if old_badge_number:
        request.session['old_badge_number'] = old_badge_number

    # Redirect ไปหน้า wizard_step1 พร้อม staff_id
    return redirect('registry:wizard_step1_edit', staff_id=staff_profile.id)

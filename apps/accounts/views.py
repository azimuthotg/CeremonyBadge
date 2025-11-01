from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from apps.registry.models import StaffProfile, BadgeRequest
from apps.badges.models import Badge

def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'ยินดีต้อนรับ, {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'บัญชีผู้ใช้ของคุณถูกระงับการใช้งาน')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'ออกจากระบบเรียบร้อยแล้ว')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard - แยกตาม Role"""
    user = request.user

    context = {
        'user': user,
    }

    # Dashboard สำหรับ Submitter
    if user.role == 'submitter':
        if user.department:
            context['total_staff'] = StaffProfile.objects.filter(department=user.department).count()
            context['pending_requests'] = BadgeRequest.objects.filter(
                staff_profile__department=user.department,
                status__in=['draft', 'photo_uploaded', 'ready_to_submit']
            ).count()
            context['submitted_requests'] = BadgeRequest.objects.filter(
                staff_profile__department=user.department,
                status='submitted'
            ).count()
            context['approved_badges'] = Badge.objects.filter(
                staff_profile__department=user.department
            ).count()

            # รายการล่าสุด
            context['recent_staff'] = StaffProfile.objects.filter(
                department=user.department
            ).order_by('-created_at')[:5]

    # Dashboard สำหรับ Officer/Admin
    elif user.role in ['officer', 'admin']:
        context['total_staff'] = StaffProfile.objects.count()
        context['pending_review'] = BadgeRequest.objects.filter(
            status__in=['submitted', 'under_review']
        ).count()
        context['approved_today'] = BadgeRequest.objects.filter(
            status='approved',
            approved_at__date=timezone.now().date()
        ).count() if BadgeRequest.objects.filter(status='approved', approved_at__isnull=False).exists() else 0
        context['total_badges'] = Badge.objects.count()
        context['printed_badges'] = Badge.objects.filter(is_printed=True).count()

        # สถิติตามประเภทบัตร
        context['badge_stats'] = Badge.objects.values('badge_type__name', 'badge_type__color_code').annotate(
            total=Count('id')
        )

        # รายการรอตรวจสอบ
        context['pending_requests_list'] = BadgeRequest.objects.filter(
            status__in=['submitted', 'under_review']
        ).select_related('staff_profile', 'staff_profile__department').order_by('-submitted_at')[:10]

    return render(request, 'dashboard/dashboard.html', context)

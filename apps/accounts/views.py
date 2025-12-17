from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from apps.registry.models import StaffProfile, BadgeRequest
from apps.badges.models import Badge
from .models import User, Department
from .forms import UserManagementForm, DepartmentForm

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


# ==============================
# USER MANAGEMENT (Admin Only)
# ==============================

@login_required
def user_list(request):
    """รายการผู้ใช้ทั้งหมด (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    users = User.objects.all().select_related('department').order_by('-date_joined')

    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)

    # Filter by department
    dept_filter = request.GET.get('department', '')
    if dept_filter:
        users = users.filter(department_id=dept_filter)

    context = {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'dept_filter': dept_filter,
        'departments': Department.objects.filter(is_active=True),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }

    return render(request, 'accounts/user_list.html', context)


@login_required
def user_add(request):
    """เพิ่มผู้ใช้ใหม่ (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserManagementForm(request.POST, is_new=True)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'เพิ่มผู้ใช้ {user.username} เรียบร้อยแล้ว')
            return redirect('accounts:user_list')
    else:
        form = UserManagementForm(is_new=True)

    context = {
        'form': form,
        'is_new': True,
    }

    return render(request, 'accounts/user_form.html', context)


@login_required
def user_edit(request, user_id):
    """แก้ไขข้อมูลผู้ใช้ (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user, is_new=False)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'แก้ไขข้อมูล {user.username} เรียบร้อยแล้ว')
            return redirect('accounts:user_list')
    else:
        form = UserManagementForm(instance=user, is_new=False)

    context = {
        'form': form,
        'user_obj': user,
        'is_new': False,
    }

    return render(request, 'accounts/user_form.html', context)


@login_required
def user_delete(request, user_id):
    """ลบผู้ใช้ (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    user = get_object_or_404(User, pk=user_id)

    # ป้องกันการลบตัวเอง
    if user == request.user:
        messages.error(request, 'ไม่สามารถลบบัญชีของตัวเองได้')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'ลบผู้ใช้ {username} เรียบร้อยแล้ว')
        return redirect('accounts:user_list')

    context = {
        'user_obj': user,
    }

    return render(request, 'accounts/user_delete_confirm.html', context)


# ==============================
# DEPARTMENT MANAGEMENT (Admin Only)
# ==============================

@login_required
def department_list(request):
    """รายการหน่วยงาน (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    departments = Department.objects.annotate(
        user_count=Count('users')
    ).order_by('-is_active', 'name')  # เรียงตามสถานะ (เปิดใช้งานก่อน) แล้วตามด้วยชื่อ

    # Search
    search = request.GET.get('search', '')
    if search:
        departments = departments.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    context = {
        'departments': departments,
        'search': search,
        'total_departments': Department.objects.count(),
        'active_departments': Department.objects.filter(is_active=True).count(),
    }

    return render(request, 'accounts/department_list.html', context)


@login_required
def department_add(request):
    """เพิ่มหน่วยงานใหม่ (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'เพิ่มหน่วยงาน {department.name} เรียบร้อยแล้ว')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm()

    context = {
        'form': form,
        'is_new': True,
    }

    return render(request, 'accounts/department_form.html', context)


@login_required
def department_edit(request, dept_id):
    """แก้ไขหน่วยงาน (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    department = get_object_or_404(Department, pk=dept_id)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'แก้ไขหน่วยงาน {department.name} เรียบร้อยแล้ว')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm(instance=department)

    context = {
        'form': form,
        'department': department,
        'is_new': False,
    }

    return render(request, 'accounts/department_form.html', context)


@login_required
def department_delete(request, dept_id):
    """ลบหน่วยงาน (Admin only)"""
    if not request.user.is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('dashboard')

    department = get_object_or_404(Department, pk=dept_id)

    # เช็คว่ามีผู้ใช้ในหน่วยงานนี้หรือไม่
    user_count = department.users.count()

    if request.method == 'POST':
        if user_count > 0:
            messages.error(request, f'ไม่สามารถลบหน่วยงานได้ เนื่องจากมีผู้ใช้ {user_count} คนอยู่ในหน่วยงานนี้')
            return redirect('accounts:department_list')

        dept_name = department.name
        department.delete()
        messages.success(request, f'ลบหน่วยงาน {dept_name} เรียบร้อยแล้ว')
        return redirect('accounts:department_list')

    context = {
        'department': department,
        'user_count': user_count,
    }

    return render(request, 'accounts/department_delete_confirm.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from functools import wraps

from apps.registry.models import BadgeRequest, StaffProfile, Photo
from apps.approvals.models import ApprovalLog
from .models import Badge, BadgeType, PrintLog
from .utils import generate_badge_image, save_badge_image, get_next_badge_number


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
def create_badge(request, request_id):
    """สร้างบัตรจากคำขอที่อนุมัติแล้ว"""
    badge_request = get_object_or_404(BadgeRequest, pk=request_id)

    # ตรวจสอบว่าอนุมัติแล้วหรือยัง
    if badge_request.status != 'approved':
        messages.error(request, 'คำขอนี้ยังไม่ได้รับการอนุมัติ')
        return redirect('approvals:approved_list')

    # ตรวจสอบว่ามีบัตรอยู่แล้วหรือไม่
    staff_profile = badge_request.staff_profile
    if hasattr(staff_profile, 'badge'):
        messages.warning(request, f'มีบัตรสำหรับ {staff_profile.full_name} อยู่แล้ว')
        return redirect('badges:badge_detail', badge_id=staff_profile.badge.id)

    try:
        from .models_signatory import BadgeSignatory
        from .utils_signature import regenerate_badge_with_signature

        # ดึงผู้เซ็นที่ active (ควรมีคนเดียว)
        signatory = BadgeSignatory.objects.filter(is_active=True).first()
        if not signatory:
            messages.error(request, 'ไม่พบผู้เซ็นบัตรในระบบ กรุณาเพิ่มผู้เซ็นก่อน')
            return redirect('approvals:approved_list')

        # 1. ดึงหมายเลขบัตรถัดไป
        badge_number = get_next_badge_number(staff_profile.badge_type)

        # 2. ดึงรูปภาพ (ถ้ามี)
        photo = None
        if staff_profile.badge_type.requires_photo():
            try:
                photo = Photo.objects.get(staff_profile=staff_profile)
            except Photo.DoesNotExist:
                messages.error(request, 'ไม่พบรูปภาพบุคลากร')
                return redirect('approvals:approved_list')

        # 3. สร้างรูปบัตร (พื้นฐาน)
        badge_img = generate_badge_image(staff_profile, badge_number, photo)

        # 4. เพิ่มข้อมูลผู้เซ็น (default: manual = เซ็นมือจริง)
        from .utils_signature import add_signature_to_badge
        badge_img = add_signature_to_badge(badge_img, signatory, include_signature_image=False)

        # 5. บันทึกรูปบัตร
        badge_file_path = save_badge_image(badge_img, badge_number)

        # 6. สร้าง Badge object พร้อมข้อมูลผู้เซ็น
        badge = Badge.objects.create(
            staff_profile=staff_profile,
            badge_type=staff_profile.badge_type,
            badge_number=badge_number,
            qr_data='',  # ไม่ใช้ QR
            qr_signature='',  # ไม่ใช้ QR
            badge_file=badge_file_path,
            signature_type='manual',  # Default: เซ็นมือจริง
            signatory=signatory,
            created_by=request.user
        )

        # 7. อัปเดตสถานะคำขอเป็น 'badge_created'
        previous_status = badge_request.status
        badge_request.status = 'badge_created'
        badge_request.save()

        # 8. บันทึก log
        ApprovalLog.objects.create(
            badge_request=badge_request,
            action='badge_created',
            previous_status=previous_status,
            new_status='badge_created',
            comment=f'สร้างบัตรหมายเลข {badge_number} (ผู้เซ็น: {signatory.full_name})',
            performed_by=request.user,
            ip_address=get_client_ip(request)
        )

        messages.success(request, f'สร้างบัตรหมายเลข {badge_number} พร้อมข้อมูลผู้เซ็น {signatory.full_name} สำเร็จ')
        return redirect('badges:badge_detail', badge_id=badge.id)

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาดในการสร้างบัตร: {str(e)}')
        return redirect('approvals:approved_list')


@login_required
@officer_required
def badge_list(request):
    """รายการบัตรทั้งหมด"""
    badges = Badge.objects.select_related(
        'staff_profile__department',
        'staff_profile__badge_type',
        'badge_type',
        'created_by'
    ).order_by('-created_at')

    # Search
    search = request.GET.get('search', '')
    if search:
        badges = badges.filter(
            Q(badge_number__icontains=search) |
            Q(staff_profile__first_name__icontains=search) |
            Q(staff_profile__last_name__icontains=search)
        )

    # Filter by badge type
    badge_type_id = request.GET.get('badge_type')
    if badge_type_id:
        badges = badges.filter(badge_type_id=badge_type_id)

    # Filter by printed status
    printed_filter = request.GET.get('printed')
    if printed_filter == 'yes':
        badges = badges.filter(is_printed=True)
    elif printed_filter == 'no':
        badges = badges.filter(is_printed=False)

    # Get badge types for filter
    badge_types = BadgeType.objects.filter(is_active=True)

    context = {
        'badges': badges,
        'badge_types': badge_types,
        'search': search,
        'selected_badge_type': badge_type_id,
        'selected_printed': printed_filter,
    }

    return render(request, 'badges/badge_list.html', context)


@login_required
@officer_required
def badge_detail(request, badge_id):
    """รายละเอียดบัตร"""
    badge = get_object_or_404(
        Badge.objects.select_related(
            'staff_profile__department',
            'staff_profile__badge_type',
            'staff_profile__zone',
            'badge_type',
            'created_by'
        ),
        pk=badge_id
    )

    # Get photo
    photo = None
    try:
        photo = Photo.objects.get(staff_profile=badge.staff_profile)
    except Photo.DoesNotExist:
        pass

    # Get print logs
    print_logs = PrintLog.objects.filter(badge=badge).select_related('printed_by').order_by('-printed_at')

    context = {
        'badge': badge,
        'photo': photo,
        'print_logs': print_logs,
    }

    return render(request, 'badges/badge_detail.html', context)


@login_required
@officer_required
def update_signature(request, badge_id):
    """เปลี่ยนประเภทลายเซ็นบัตร (manual ↔ electronic)"""
    if request.method != 'POST':
        return redirect('badges:badge_detail', badge_id=badge_id)

    badge = get_object_or_404(Badge, pk=badge_id)

    # ดึงข้อมูลจากฟอร์ม
    signature_type = request.POST.get('signature_type', 'manual')

    # ตรวจสอบว่ามีผู้เซ็นหรือไม่
    if not badge.signatory:
        messages.error(request, 'ไม่พบข้อมูลผู้เซ็นบัตร')
        return redirect('badges:badge_detail', badge_id=badge_id)

    try:
        from .utils_signature import regenerate_badge_with_signature

        # สร้างบัตรใหม่ตามประเภทลายเซ็นที่เลือก
        badge_file_path = regenerate_badge_with_signature(badge, badge.signatory, signature_type)

        # อัปเดตบัตร
        badge.badge_file = badge_file_path
        badge.signature_type = signature_type
        badge.save()

        if signature_type == 'electronic':
            messages.success(request, f'เปลี่ยนเป็นลายเซ็นอิเล็กทรอนิกส์เรียบร้อยแล้ว')
        else:
            messages.success(request, f'เปลี่ยนเป็นเซ็นมือจริงเรียบร้อยแล้ว')

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาดในการเปลี่ยนประเภทลายเซ็น: {str(e)}')

    return redirect('badges:badge_detail', badge_id=badge_id)


@login_required
@officer_required
def print_badge(request, badge_id):
    """บันทึกการพิมพ์บัตร"""
    if request.method != 'POST':
        return redirect('badges:badge_detail', badge_id=badge_id)

    badge = get_object_or_404(Badge, pk=badge_id)

    # ดึงข้อมูลจากฟอร์ม
    notes = request.POST.get('notes', '')

    # สร้าง print log
    print_log = PrintLog.objects.create(
        badge=badge,
        printed_by=request.user,
        notes=notes,
        signature_type=badge.signature_type,
        signatory=badge.signatory
    )

    # อัปเดตสถานะ
    badge.is_printed = True
    badge.printed_count += 1
    badge.save()

    # อัปเดตสถานะ badge request (ถ้ามี)
    try:
        badge_request = BadgeRequest.objects.get(staff_profile=badge.staff_profile)
        if badge_request.status == 'badge_created':
            previous_status = badge_request.status
            badge_request.status = 'printed'
            badge_request.save()

            # บันทึก log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='printed',
                previous_status=previous_status,
                new_status='printed',
                comment=f'พิมพ์บัตรครั้งที่ {badge.printed_count} ({badge.signature_type})',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )
    except BadgeRequest.DoesNotExist:
        pass

    messages.success(request, f'บันทึกการพิมพ์บัตรหมายเลข {badge.badge_number} แล้ว')
    return redirect('badges:badge_detail', badge_id=badge_id)


@login_required
@officer_required
def delete_badge(request, badge_id):
    """ลบบัตร"""
    if request.method != 'POST':
        return redirect('badges:badge_list')

    badge = get_object_or_404(Badge, pk=badge_id)

    # เก็บข้อมูลก่อนลบ
    badge_number = badge.badge_number
    staff_name = badge.staff_profile.full_name

    # ลบไฟล์รูปบัตร
    if badge.badge_file:
        try:
            import os
            if os.path.exists(badge.badge_file.path):
                os.remove(badge.badge_file.path)
        except Exception as e:
            print(f"Error deleting badge file: {e}")

    # ลบ QR code (ถ้ามี)
    if badge.qr_code:
        try:
            import os
            if os.path.exists(badge.qr_code.path):
                os.remove(badge.qr_code.path)
        except Exception as e:
            print(f"Error deleting QR code: {e}")

    # อัปเดตสถานะ badge request กลับเป็น approved (ถ้าต้องการสร้างใหม่)
    try:
        badge_request = BadgeRequest.objects.get(staff_profile=badge.staff_profile)
        if badge_request.status in ['badge_created', 'printed']:
            badge_request.status = 'approved'
            badge_request.save()

            # บันทึก log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='badge_deleted',
                previous_status='badge_created',
                new_status='approved',
                comment=f'ลบบัตรหมายเลข {badge_number}',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )
    except BadgeRequest.DoesNotExist:
        pass

    # ลบบัตร
    badge.delete()

    messages.success(request, f'ลบบัตรหมายเลข {badge_number} ({staff_name}) เรียบร้อยแล้ว')
    return redirect('badges:badge_list')

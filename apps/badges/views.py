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
        if staff_profile.badge_type.requires_photo:
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
def bulk_create_badge(request):
    """สร้างบัตรหลายรายการพร้อมกัน"""
    if request.method != 'POST':
        return redirect('approvals:approved_list')

    request_ids = request.POST.getlist('request_ids')
    if not request_ids:
        messages.error(request, 'กรุณาเลือกรายการที่ต้องการสร้างบัตร')
        return redirect('approvals:approved_list')

    # ดึงผู้เซ็นที่ active
    from .models_signatory import BadgeSignatory
    signatory = BadgeSignatory.objects.filter(is_active=True).first()
    if not signatory:
        messages.error(request, 'ไม่พบผู้เซ็นบัตรในระบบ กรุณาเพิ่มผู้เซ็นก่อน')
        return redirect('approvals:approved_list')

    success_count = 0
    skip_count = 0
    error_count = 0
    error_messages = []

    for request_id in request_ids:
        try:
            badge_request = BadgeRequest.objects.get(pk=request_id)

            # ตรวจสอบสถานะ
            if badge_request.status != 'approved':
                skip_count += 1
                continue

            # ตรวจสอบว่ามีบัตรอยู่แล้วหรือไม่
            staff_profile = badge_request.staff_profile
            if hasattr(staff_profile, 'badge'):
                skip_count += 1
                continue

            # ตรวจสอบรูปภาพ (ถ้าต้องการ)
            photo = None
            if staff_profile.badge_type.requires_photo:
                try:
                    photo = Photo.objects.get(staff_profile=staff_profile)
                except Photo.DoesNotExist:
                    error_messages.append(f'{staff_profile.full_name}: ไม่พบรูปภาพ')
                    error_count += 1
                    continue

            # สร้างบัตร
            badge_number = get_next_badge_number(staff_profile.badge_type)
            badge_img = generate_badge_image(staff_profile, badge_number, photo)

            # เพิ่มข้อมูลผู้เซ็น
            from .utils_signature import add_signature_to_badge
            badge_img = add_signature_to_badge(badge_img, signatory, include_signature_image=False)

            # บันทึกรูปบัตร
            badge_file_path = save_badge_image(badge_img, badge_number)

            # สร้าง Badge object
            badge = Badge.objects.create(
                staff_profile=staff_profile,
                badge_type=staff_profile.badge_type,
                badge_number=badge_number,
                qr_data='',
                qr_signature='',
                badge_file=badge_file_path,
                signature_type='manual',
                signatory=signatory,
                created_by=request.user
            )

            # อัปเดตสถานะ
            previous_status = badge_request.status
            badge_request.status = 'badge_created'
            badge_request.save()

            # บันทึก log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='badge_created',
                previous_status=previous_status,
                new_status='badge_created',
                comment=f'สร้างบัตรหมายเลข {badge_number} (Bulk)',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )

            success_count += 1

        except BadgeRequest.DoesNotExist:
            error_count += 1
        except Exception as e:
            error_messages.append(f'ID {request_id}: {str(e)}')
            error_count += 1

    # แสดงผลลัพธ์
    if success_count > 0:
        messages.success(request, f'สร้างบัตรสำเร็จ {success_count} รายการ')
    if skip_count > 0:
        messages.info(request, f'ข้ามรายการที่มีบัตรแล้วหรือสถานะไม่เหมาะสม {skip_count} รายการ')
    if error_count > 0:
        messages.warning(request, f'พบข้อผิดพลาด {error_count} รายการ')
        for error_msg in error_messages[:5]:  # แสดงแค่ 5 รายการแรก
            messages.error(request, error_msg)

    return redirect('approvals:approved_list')


@login_required
@officer_required
def badge_list(request):
    """รายการบัตรพร้อมพิมพ์ (แยก Tab ตามสีบัตร)"""
    from django.db.models import Case, When, IntegerField
    from apps.badges.utils import get_next_badge_number
    from apps.accounts.models import Department

    # Search and Filter
    search = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')

    # Get all departments for filter dropdown
    departments = Department.objects.filter(is_active=True).order_by('name')

    # Get all badge types (เรียงตามลำดับ: ชมพู แดง เหลือง เขียว)
    badge_order = Case(
        When(name='บัตรชมพู', then=1),
        When(name='บัตรแดง', then=2),
        When(name='บัตรเหลือง', then=3),
        When(name='บัตรเขียว', then=4),
        default=5,
        output_field=IntegerField(),
    )
    badge_types = BadgeType.objects.filter(is_active=True).order_by(badge_order)

    # แยกข้อมูลตามประเภทบัตร
    badge_data = []
    badge_info = []

    for badge_type in badge_types:
        # ดึงบัตรทั้งหมดของประเภทนี้ - เฉพาะหน่วยงานที่เปิดใช้งาน
        all_badges = Badge.objects.filter(
            badge_type=badge_type,
            staff_profile__department__is_active=True
        ).select_related(
            'staff_profile__department',
            'staff_profile__badge_type',
            'badge_type',
            'created_by'
        ).order_by('-created_at')

        # Filter by search
        if search:
            all_badges = all_badges.filter(
                Q(badge_number__icontains=search) |
                Q(staff_profile__first_line__icontains=search) |
                Q(staff_profile__last_line__icontains=search)
            )

        # Filter by department
        if department_filter:
            all_badges = all_badges.filter(staff_profile__department_id=department_filter)

        # นับจำนวนที่พิมพ์แล้ว
        printed_count = all_badges.filter(is_printed=True).count()
        total_count = all_badges.count()

        # หาเลขบัตรล่าสุดและเลขบัตรถัดไป
        latest_badge = Badge.objects.filter(badge_type=badge_type).order_by('-created_at').first()
        latest_badge_number = latest_badge.badge_number if latest_badge else '-'
        next_badge_number = get_next_badge_number(badge_type)

        badge_data.append({
            'badge_type': badge_type,
            'badges': all_badges,
            'printed_count': printed_count,
            'total_count': total_count,
        })

        badge_info.append({
            'badge_type': badge_type,
            'latest_badge_number': latest_badge_number,
            'next_badge_number': next_badge_number,
        })

    # Tab ที่เลือก (default = บัตรแรก)
    active_badge_id = request.GET.get('badge', '')
    if not active_badge_id and badge_types.exists():
        active_badge_id = str(badge_types.first().id)

    context = {
        'badge_data': badge_data,
        'badge_info': badge_info,
        'active_badge_id': active_badge_id,
        'search': search,
        'departments': departments,
        'department_filter': department_filter,
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
def edit_badge(request, badge_id):
    """แก้ไขข้อมูลบัตร"""
    badge = get_object_or_404(Badge, pk=badge_id)
    staff_profile = badge.staff_profile

    # Get all active badge types
    from django.db.models import Case, When, IntegerField
    badge_order = Case(
        When(name='บัตรชมพู', then=1),
        When(name='บัตรแดง', then=2),
        When(name='บัตรเหลือง', then=3),
        When(name='บัตรเขียว', then=4),
        default=5,
        output_field=IntegerField(),
    )
    badge_types = BadgeType.objects.filter(is_active=True).order_by(badge_order)

    # Get all active zones
    from apps.registry.models import Zone
    zones = Zone.objects.filter(is_active=True).order_by('order', 'code')

    # Get all active departments
    from apps.accounts.models import Department
    departments = Department.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        # Get form data
        display_name = request.POST.get('display_name', '').strip()
        zone_id = request.POST.get('zone')
        department_id = request.POST.get('department')
        new_badge_type_id = request.POST.get('badge_type')
        revision_reason = request.POST.get('revision_reason', '').strip()

        # Validate
        if not revision_reason:
            messages.error(request, 'กรุณาระบุเหตุผลในการแก้ไข')
            return redirect('badges:edit_badge', badge_id=badge_id)

        # Check if badge type changed (color change)
        color_changed = False
        old_badge_number = badge.badge_number
        old_badge_type = badge.badge_type

        if new_badge_type_id and int(new_badge_type_id) != badge.badge_type.id:
            color_changed = True
            new_badge_type = BadgeType.objects.get(pk=new_badge_type_id)

        try:
            # เก็บค่าเดิมก่อนอัพเดต (สำหรับ log และตรวจสอบการเปลี่ยนแปลง)
            old_display_name = staff_profile.display_name
            old_zone = staff_profile.zone
            old_department = staff_profile.department

            # Update staff profile
            # อัปเดต display_name ทุกกรณี (รวมค่าว่างด้วย - เพื่อให้กลับไปใช้ชื่อเต็ม)
            staff_profile.display_name = display_name if display_name else None

            # อัปเดต zone เฉพาะเมื่อมีการส่งค่ามา
            # ถ้า zone_id เป็นค่าว่าง ("") ให้เซ็ตเป็น None
            if zone_id:
                staff_profile.zone_id = zone_id
            else:
                # ถ้าไม่เลือก (ค่าว่าง) ให้เคลียร์โซน
                staff_profile.zone_id = None

            # อัปเดต department (ถ้ามีการส่งค่ามา)
            if department_id:
                staff_profile.department_id = department_id

            # If color changed, update badge type in staff profile
            if color_changed:
                staff_profile.badge_type = new_badge_type

            staff_profile.save()

            # ตรวจสอบว่ามีการเปลี่ยนแปลงข้อมูลที่แสดงบนบัตรหรือไม่
            # (display_name หรือ zone เท่านั้น - department ไม่แสดงบนบัตร)
            display_changed = (old_display_name != staff_profile.display_name)
            zone_changed = (old_zone != staff_profile.zone)
            department_changed = (old_department != staff_profile.department)
            needs_regenerate = display_changed or zone_changed

            # Reload staff_profile to ensure we have the latest data
            staff_profile.refresh_from_db()

            # Update badge
            badge.revision_count += 1
            badge.revision_reason = revision_reason

            # If color changed, generate new badge number and recreate badge
            if color_changed:
                # เก็บข้อมูลบัตรเก่า (ก่อน delete)
                old_badge_id = badge.id
                old_signatory = badge.signatory
                old_signature_type = badge.signature_type
                old_created_by = badge.created_by
                old_revision_count = badge.revision_count + 1  # +1 เพราะนี่คือการแก้ไขครั้งใหม่

                # ลบบัตรเดิมออก (เพราะ badge_number เป็น unique)
                badge.delete()

                # Get new badge number
                new_badge_number = get_next_badge_number(new_badge_type)

                # Regenerate badge image
                photo = None
                if new_badge_type.requires_photo:
                    try:
                        photo = Photo.objects.get(staff_profile=staff_profile)
                    except Photo.DoesNotExist:
                        pass

                # Generate new badge image
                badge_img = generate_badge_image(staff_profile, new_badge_number, photo)

                # Add signature
                if old_signatory:
                    from .utils_signature import add_signature_to_badge
                    include_sig_image = (old_signature_type == 'electronic')
                    badge_img = add_signature_to_badge(badge_img, old_signatory, include_sig_image)

                # Save new badge file
                badge_file_path = save_badge_image(badge_img, new_badge_number)

                # สร้างบัตรใหม่
                badge = Badge.objects.create(
                    staff_profile=staff_profile,
                    badge_type=new_badge_type,
                    badge_number=new_badge_number,
                    qr_data='',
                    qr_signature='',
                    badge_file=badge_file_path,
                    signature_type=old_signature_type,
                    signatory=old_signatory,
                    is_printed=False,  # ต้องพิมพ์ใหม่
                    printed_count=0,
                    revision_count=old_revision_count,
                    revision_reason=revision_reason,
                    created_by=old_created_by
                )

                # Log color change
                ApprovalLog.objects.create(
                    badge_request=BadgeRequest.objects.get(staff_profile=staff_profile),
                    action='change_color',
                    previous_status='badge_created',
                    new_status='badge_created',
                    comment=f'เปลี่ยนสีบัตร: {old_badge_type.name} ({old_badge_number}) → {new_badge_type.name} ({new_badge_number}) | เหตุผล: {revision_reason}',
                    performed_by=request.user,
                    ip_address=get_client_ip(request)
                )

                messages.success(request, f'เปลี่ยนสีบัตรสำเร็จ: {old_badge_type.name} ({old_badge_number}) → {new_badge_type.name} ({new_badge_number})')
            else:
                # Normal edit - regenerate badge only if display_name or zone changed
                if needs_regenerate:
                    # Regenerate badge with same number
                    photo = None
                    if badge.badge_type.requires_photo:
                        try:
                            photo = Photo.objects.get(staff_profile=staff_profile)
                        except Photo.DoesNotExist:
                            pass

                    # Generate badge image
                    badge_img = generate_badge_image(staff_profile, badge.badge_number, photo)

                    # Add signature
                    if badge.signatory:
                        from .utils_signature import add_signature_to_badge
                        include_sig_image = (badge.signature_type == 'electronic')
                        badge_img = add_signature_to_badge(badge_img, badge.signatory, include_sig_image)

                    # Save badge file
                    badge_file_path = save_badge_image(badge_img, badge.badge_number)
                    badge.badge_file = badge_file_path

                    badge.save()

                # สร้าง log comment ตามการเปลี่ยนแปลง
                changes = []
                if display_changed:
                    changes.append(f'ชื่อบนบัตร: "{old_display_name or staff_profile.full_name}" → "{staff_profile.display_name or staff_profile.full_name}"')
                if zone_changed:
                    old_zone_text = f'{old_zone.code} - {old_zone.name}' if old_zone else '-'
                    new_zone_text = f'{staff_profile.zone.code} - {staff_profile.zone.name}' if staff_profile.zone else '-'
                    changes.append(f'โซน: {old_zone_text} → {new_zone_text}')
                if department_changed:
                    changes.append(f'หน่วยงาน: {old_department.name} → {staff_profile.department.name}')

                change_summary = ', '.join(changes) if changes else 'ไม่มีการเปลี่ยนแปลง'

                # Log edit
                ApprovalLog.objects.create(
                    badge_request=BadgeRequest.objects.get(staff_profile=staff_profile),
                    action='edit_badge',
                    previous_status='badge_created',
                    new_status='badge_created',
                    comment=f'แก้ไขบัตรหมายเลข {badge.badge_number} (ครั้งที่ {badge.revision_count}) | การเปลี่ยนแปลง: {change_summary} | เหตุผล: {revision_reason}',
                    performed_by=request.user,
                    ip_address=get_client_ip(request)
                )

                success_msg = f'แก้ไขบัตรหมายเลข {badge.badge_number} สำเร็จ (ครั้งที่ {badge.revision_count})'
                if needs_regenerate:
                    success_msg += ' - สร้างบัตรใหม่แล้ว'
                elif department_changed:
                    success_msg += ' - อัพเดตหน่วยงานแล้ว (ไม่ต้องพิมพ์บัตรใหม่)'
                messages.success(request, success_msg)

            return redirect('badges:badge_detail', badge_id=badge.id)

        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาดในการแก้ไขบัตร: {str(e)}')

            # If color was changed, the old badge was deleted, so redirect to badge list
            # instead of trying to redirect to the deleted badge
            if color_changed:
                return redirect('badges:badge_list')
            else:
                return redirect('badges:edit_badge', badge_id=badge_id)

    # GET request - show form
    context = {
        'badge': badge,
        'staff_profile': staff_profile,
        'badge_types': badge_types,
        'zones': zones,
        'departments': departments,
    }

    return render(request, 'badges/edit_badge.html', context)


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


@login_required
@officer_required
def bulk_delete_badge(request):
    """ลบบัตรหลายรายการ"""
    if request.method != 'POST':
        return redirect('badges:badge_list')

    badge_ids = request.POST.getlist('badge_ids')

    if not badge_ids:
        messages.error(request, 'กรุณาเลือกบัตรที่ต้องการลบ')
        return redirect('badges:badge_list')

    success_count = 0
    error_count = 0

    for badge_id in badge_ids:
        try:
            badge = Badge.objects.get(pk=badge_id)

            # เก็บข้อมูลก่อนลบ
            badge_number = badge.badge_number

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

            # อัปเดตสถานะ badge request กลับเป็น approved
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
                        comment=f'ลบบัตรหมายเลข {badge_number} (Bulk)',
                        performed_by=request.user,
                        ip_address=get_client_ip(request)
                    )
            except BadgeRequest.DoesNotExist:
                pass

            # ลบบัตร
            badge.delete()
            success_count += 1

        except Badge.DoesNotExist:
            error_count += 1
        except Exception as e:
            print(f"Error deleting badge {badge_id}: {e}")
            error_count += 1

    # แสดงผลลัพธ์
    if success_count > 0:
        messages.success(request, f'ลบบัตรสำเร็จ {success_count} รายการ')
    if error_count > 0:
        messages.warning(request, f'ลบบัตรไม่สำเร็จ {error_count} รายการ')

    return redirect('badges:badge_list')


@login_required
@officer_required
def bulk_reset_print(request):
    """Reset สถานะการพิมพ์ของบัตรหลายรายการ"""
    if request.method != 'POST':
        return redirect('badges:badge_list')

    badge_ids = request.POST.getlist('badge_ids')

    if not badge_ids:
        messages.error(request, 'กรุณาเลือกบัตรที่ต้องการ Reset การพิมพ์')
        return redirect('badges:badge_list')

    success_count = 0
    error_count = 0

    for badge_id in badge_ids:
        try:
            badge = Badge.objects.get(pk=badge_id)

            # เก็บข้อมูลเดิม
            badge_number = badge.badge_number
            old_printed_count = badge.printed_count

            # Reset สถานะการพิมพ์
            badge.is_printed = False
            badge.printed_count = 0
            badge.save()

            # อัปเดตสถานะ badge request กลับเป็น badge_created
            try:
                badge_request = BadgeRequest.objects.get(staff_profile=badge.staff_profile)
                if badge_request.status == 'printed':
                    previous_status = badge_request.status
                    badge_request.status = 'badge_created'
                    badge_request.save()

                    # บันทึก log
                    ApprovalLog.objects.create(
                        badge_request=badge_request,
                        action='reset_print',
                        previous_status=previous_status,
                        new_status='badge_created',
                        comment=f'Reset การพิมพ์บัตรหมายเลข {badge_number} (เคยพิมพ์ {old_printed_count} ครั้ง)',
                        performed_by=request.user,
                        ip_address=get_client_ip(request)
                    )
            except BadgeRequest.DoesNotExist:
                pass

            success_count += 1

        except Badge.DoesNotExist:
            error_count += 1
        except Exception as e:
            print(f"Error resetting badge {badge_id}: {e}")
            error_count += 1

    # แสดงผลลัพธ์
    if success_count > 0:
        messages.success(request, f'Reset การพิมพ์สำเร็จ {success_count} รายการ')
    if error_count > 0:
        messages.warning(request, f'Reset การพิมพ์ไม่สำเร็จ {error_count} รายการ')

    return redirect('badges:badge_list')

# ==========================================
# Print Manager (A4 Layout - 8 badges)
# ==========================================

@login_required
@officer_required
def print_manager(request):
    """
    หน้าจัดการพิมพ์บัตรแบบ A4 (8 ใบต่อแผ่น)
    - แสดงรายการบัตรแยกตาม tabs สี (ชมพู, แดง, เหลือง, เขียว)
    - Shopping Cart สำหรับเลือกบัตรสูงสุด 8 ใบ
    - สามารถเลือกบัตรจากหลายสีมาพิมพ์ในแผ่นเดียวกันได้
    """
    from django.db.models import Q, Case, When, IntegerField
    from apps.accounts.models import Department

    # Get filter parameters
    department_filter = request.GET.get('department', '')

    # Get all departments for filter dropdown
    departments = Department.objects.filter(is_active=True).order_by('name')

    # Get all badge types (ordered by color)
    badge_order = Case(
        When(name='บัตรชมพู', then=1),
        When(name='บัตรแดง', then=2),
        When(name='บัตรเหลือง', then=3),
        When(name='บัตรเขียว', then=4),
        default=5,
        output_field=IntegerField(),
    )
    badge_types = BadgeType.objects.filter(is_active=True).order_by(badge_order)

    # Get badges for each type (active badges only)
    badges_by_type = {}
    for badge_type in badge_types:
        # เรียงลำดับ: ยังไม่พิมพ์ขึ้นก่อน (is_printed=False) แล้วค่อยที่พิมพ์แล้ว - เฉพาะหน่วยงานที่เปิดใช้งาน
        badges = Badge.objects.filter(
            badge_type=badge_type,
            is_active=True,
            staff_profile__department__is_active=True
        ).select_related(
            'staff_profile',
            'staff_profile__department',
            'signatory'
        ).order_by('is_printed', 'badge_number')  # is_printed=False (0) ขึ้นก่อน True (1)

        # Filter by department
        if department_filter:
            badges = badges.filter(staff_profile__department_id=department_filter)

        # นับจำนวนแยกตามสถานะ
        total_count = badges.count()
        printed_count = badges.filter(is_printed=True).count()
        unprinted_count = total_count - printed_count

        badges_by_type[badge_type.color] = {
            'badge_type': badge_type,
            'badges': badges,
            'total_count': total_count,
            'printed_count': printed_count,
            'unprinted_count': unprinted_count,
        }

    context = {
        'badge_types': badge_types,
        'badges_by_type': badges_by_type,
        'departments': departments,
        'department_filter': department_filter,
    }

    return render(request, 'badges/print_manager.html', context)


@login_required
@officer_required
def print_preview(request):
    """
    API สำหรับแสดง preview บัตรที่เลือก (AJAX)
    รับ badge IDs มาแสดงภาพตัวอย่าง layout A4
    """
    import json
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        badge_ids = data.get('badge_ids', [])
        
        if len(badge_ids) > 8:
            return JsonResponse({'error': 'สามารถเลือกได้สูงสุด 8 บัตรเท่านั้น'}, status=400)
        
        # Get badge details
        badges = Badge.objects.filter(id__in=badge_ids).select_related(
            'badge_type', 'staff_profile'
        )
        
        badge_data = []
        for badge in badges:
            badge_data.append({
                'id': badge.id,
                'badge_number': badge.badge_number,
                'staff_name': badge.staff_profile.full_name,
                'badge_type_name': badge.badge_type.name,
                'badge_type_color': badge.badge_type.color_code,
                'image_url': badge.badge_file.url if badge.badge_file else None,
            })
        
        return JsonResponse({
            'success': True,
            'badges': badge_data,
            'total': len(badge_data)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@officer_required  
def generate_print_pdf(request):
    """
    สร้างไฟล์ PDF A4 สำหรับพิมพ์บัตร 8 ใบ
    Layout: 2 คอลัมน์ x 4 แถว = 8 badges
    """
    import json
    from django.http import JsonResponse, FileResponse
    from io import BytesIO
    from PIL import Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        badge_ids = data.get('badge_ids', [])
        
        if not badge_ids:
            return JsonResponse({'error': 'กรุณาเลือกบัตรที่ต้องการพิมพ์'}, status=400)
        
        if len(badge_ids) > 8:
            return JsonResponse({'error': 'สามารถเลือกได้สูงสุด 8 บัตรเท่านั้น'}, status=400)
        
        # Get badges
        badges = Badge.objects.filter(id__in=badge_ids).select_related('staff_profile')
        
        if not badges.exists():
            return JsonResponse({'error': 'ไม่พบบัตรที่เลือก'}, status=404)
        
        # Create PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        page_width, page_height = A4
        
        # Badge dimensions (1122 x 768 px → convert to mm)
        # A4 = 210mm x 297mm
        # เนื่องจาก template PNG มีพื้นขาวรอบๆ ให้ใช้ negative spacing เพื่อให้บัตรทับกัน
        # ความกว้างบัตร = 210 / 2 = 105mm
        # ความสูงบัตร = 297 / 4 = 74.25mm
        badge_width_mm = 105 * mm
        badge_height_mm = 74.25 * mm

        # Margins - ไม่มี margin
        margin_x = 0
        margin_y = 0

        # Spacing between badges - ใช้ NEGATIVE spacing เพื่อให้บัตรทับกัน/ชิดกัน
        # ปรับค่าให้พอดีกับขอบบัตร ไม่ทับเข้าไปในเนื้อหา
        spacing_x = -0.3 * mm  # ลบ 0.5mm ให้ซ้าย-ขวาชิดกัน
        spacing_y = -0.7 * mm  # ลบ 0.8mm ให้บน-ล่างชิดกันมากกว่า
        
        # Calculate positions (2 columns x 4 rows)
        positions = []
        for row in range(4):
            for col in range(2):
                x = margin_x + col * (badge_width_mm + spacing_x)
                # Start from top
                y = page_height - margin_y - (row + 1) * badge_height_mm - row * spacing_y
                positions.append((x, y))
        
        # Add badges to PDF
        for idx, badge in enumerate(badges[:8]):  # Max 8 badges
            if idx >= len(positions):
                break
            
            x, y = positions[idx]
            
            # Draw badge image
            if badge.badge_file:
                try:
                    badge_img_path = badge.badge_file.path
                    # ปิด preserveAspectRatio เพื่อให้รูปยืดเต็มพื้นที่ ไม่มี margin
                    pdf.drawImage(badge_img_path, x, y,
                                width=badge_width_mm, height=badge_height_mm,
                                preserveAspectRatio=False)  # เปลี่ยนเป็น False
                except Exception as e:
                    print(f"Error adding badge {badge.badge_number}: {e}")
        
        # Save PDF
        pdf.save()
        buffer.seek(0)
        
        # Update print count for all badges
        for badge in badges:
            badge.printed_count += 1
            badge.is_printed = True
            badge.save()
            
            # Log print action
            PrintLog.objects.create(
                badge=badge,
                printed_by=request.user,
                notes=f'พิมพ์บัตรผ่านระบบ A4 (รวม {len(badges)} ใบ)'
            )
        
        # Return PDF file
        response = FileResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="badges_print_{len(badges)}_sheets.pdf"'
        
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

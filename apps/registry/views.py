from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from PIL import Image
import os
from django.conf import settings
from functools import wraps

from .models import StaffProfile, Photo, BadgeRequest, Zone
from apps.badges.models import BadgeType
from .forms import StaffProfileForm, PhotoUploadForm, BadgeRequestReviewForm

# Decorator for admin-only views
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def staff_list(request):
    """รายการบุคลากร - แบ่งตาม Tab ประเภทบัตร"""
    user = request.user

    # Filter by department for submitters
    if user.role == 'submitter':
        base_queryset = StaffProfile.objects.filter(department=user.department).select_related(
            'badge_type', 'department', 'badge_request'
        )
    else:
        base_queryset = StaffProfile.objects.all().select_related(
            'badge_type', 'department', 'badge_request'
        )

    # Search
    search = request.GET.get('search', '')
    if search:
        base_queryset = base_queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(position__icontains=search) |
            Q(national_id__icontains=search)
        )

    # Get all badge types (เรียงตามลำดับ: ชมพู แดง เหลือง เขียว)
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

    # แยกข้อมูลตามประเภทบัตร
    badge_data = []
    for badge_type in badge_types:
        staff_list = base_queryset.filter(badge_type=badge_type).order_by('-created_at')
        total_count = staff_list.count()

        # นับจำนวนที่ส่งแล้ว (status = submitted, under_review, approved, badge_created, printed, completed)
        submitted_statuses = ['submitted', 'under_review', 'approved', 'badge_created', 'printed', 'completed']
        submitted_count = staff_list.filter(
            badge_request__status__in=submitted_statuses
        ).count()

        badge_data.append({
            'badge_type': badge_type,
            'staff_profiles': staff_list,
            'total_count': total_count,
            'submitted_count': submitted_count,
        })

    # Tab ที่เลือก (default = บัตรแรก)
    active_badge_id = request.GET.get('badge', '')
    if not active_badge_id and badge_types.exists():
        active_badge_id = str(badge_types.first().id)

    # Get bulk submit errors from session (if any)
    bulk_submit_errors = request.session.pop('bulk_submit_errors', None)

    context = {
        'badge_data': badge_data,
        'active_badge_id': active_badge_id,
        'search': search,
        'bulk_submit_errors': bulk_submit_errors,
    }

    return render(request, 'registry/staff_list.html', context)


@login_required
def wizard_step1(request, staff_id=None):
    """Step 1: ข้อมูลบุคลากร"""
    # Check if user has department (for submitters)
    if request.user.role == 'submitter' and not request.user.department:
        messages.error(request, 'คุณยังไม่ได้ระบุหน่วยงาน กรุณาติดต่อผู้ดูแลระบบ')
        return redirect('dashboard')

    # Check if editing existing staff
    staff_profile = None
    is_edit_mode = False
    if staff_id:
        staff_profile = get_object_or_404(StaffProfile, pk=staff_id)
        is_edit_mode = True
        # Check permission
        if request.user.role == 'submitter' and staff_profile.department != request.user.department:
            messages.error(request, 'คุณไม่มีสิทธิ์แก้ไขข้อมูลนี้')
            return redirect('registry:staff_list')

    if request.method == 'POST':
        form = StaffProfileForm(
            request.POST,
            instance=staff_profile,
            user_role=request.user.role,
            is_edit_mode=is_edit_mode
        )
        if form.is_valid():
            staff = form.save(commit=False)
            # Set department from user if creating new and user is submitter
            if not staff_id:
                if request.user.role == 'submitter':
                    staff.department = request.user.department
                staff.created_by = request.user
            staff.save()

            messages.success(request, 'บันทึกข้อมูลบุคลากรเรียบร้อยแล้ว')

            # ตรวจสอบว่าเป็นการแก้ไขจากหน้า approved list หรือไม่
            edit_from_approved = request.session.get('edit_from_approved', False)
            if edit_from_approved:
                # ดึงข้อมูลจาก session
                edit_request_id = request.session.get('edit_request_id')
                has_badge = request.session.get('has_badge', False)
                old_badge_number = request.session.get('old_badge_number')

                # ถ้ามีบัตรแล้ว ให้สร้างบัตรใหม่ทับเดิมโดยใช้หมายเลขเดิม
                if has_badge and old_badge_number:
                    try:
                        from apps.badges.models import Badge
                        from apps.badges.utils import generate_badge_image, save_badge_image
                        from apps.approvals.models import ApprovalLog
                        import os
                        from django.conf import settings

                        # ดึงข้อมูล badge และ photo
                        badge = Badge.objects.get(staff_profile=staff)
                        try:
                            photo = Photo.objects.get(staff_profile=staff)
                        except Photo.DoesNotExist:
                            photo = None

                        # สร้างรูปบัตรใหม่ด้วยหมายเลขเดิม
                        badge_img = generate_badge_image(staff, old_badge_number, photo)

                        # บันทึกทับไฟล์เดิม
                        badges_dir = os.path.join(settings.MEDIA_ROOT, 'badges', 'generated')
                        os.makedirs(badges_dir, exist_ok=True)
                        filename = f'badge_{old_badge_number}.png'
                        filepath = os.path.join(badges_dir, filename)
                        badge_img.save(filepath, 'PNG', quality=95)

                        # อัปเดต badge record (ไม่เปลี่ยนหมายเลข)
                        badge.save()

                        messages.success(request, f'แก้ไขข้อมูลและสร้างบัตรใหม่ทับเดิม (หมายเลข {old_badge_number}) เรียบร้อยแล้ว')

                        # บันทึก log การแก้ไข
                        if edit_request_id:
                            badge_request = BadgeRequest.objects.get(pk=edit_request_id)
                            ApprovalLog.objects.create(
                                badge_request=badge_request,
                                action='edit',
                                previous_status=badge_request.status,
                                new_status=badge_request.status,
                                comment='แก้ไขข้อมูลและสร้างบัตรใหม่ทับเดิม',
                                performed_by=request.user,
                                ip_address=get_client_ip(request)
                            )

                    except Badge.DoesNotExist:
                        messages.warning(request, 'ไม่พบข้อมูลบัตร แก้ไขข้อมูลเรียบร้อยแล้ว')
                    except Exception as e:
                        messages.error(request, f'เกิดข้อผิดพลาดในการสร้างบัตรใหม่: {str(e)}')
                else:
                    # ไม่มีบัตร แค่บันทึก log การแก้ไข
                    if edit_request_id:
                        from apps.approvals.models import ApprovalLog
                        badge_request = BadgeRequest.objects.get(pk=edit_request_id)
                        ApprovalLog.objects.create(
                            badge_request=badge_request,
                            action='edit',
                            previous_status=badge_request.status,
                            new_status=badge_request.status,
                            comment='แก้ไขข้อมูลบุคลากร',
                            performed_by=request.user,
                            ip_address=get_client_ip(request)
                        )

                # ลบ session flags
                request.session.pop('edit_from_approved', None)
                request.session.pop('edit_request_id', None)
                request.session.pop('has_badge', None)
                request.session.pop('old_badge_number', None)

                # Redirect กลับไปหน้า approved list
                return redirect('approvals:approved_list')

            # ถ้าเป็นโหมดแก้ไข ให้กลับไปหน้ารายละเอียด
            if is_edit_mode:
                return redirect('registry:staff_detail', staff_id=staff.id)

            # ถ้าเป็น yellow หรือ green ไม่ต้องอัปโหลดรูป ข้ามไป step 3 เลย
            if not staff.badge_type.requires_photo():
                # สร้าง BadgeRequest ถ้ายังไม่มี หรือ update status ถ้ามีแล้ว
                badge_request, created = BadgeRequest.objects.get_or_create(
                    staff_profile=staff,
                    defaults={'status': 'ready_to_submit', 'created_by': request.user}
                )
                # Update status เป็น ready_to_submit (กรณี import มาเป็น draft)
                if badge_request.status in ['draft', 'photo_uploaded']:
                    badge_request.status = 'ready_to_submit'
                    badge_request.save()

                messages.info(request, f'บัตรประเภท {staff.badge_type.name} ไม่ต้องการรูปภาพ')
                return redirect('registry:wizard_step3', staff_id=staff.id)

            return redirect('registry:wizard_step2', staff_id=staff.id)
    else:
        form = StaffProfileForm(
            instance=staff_profile,
            user_role=request.user.role,
            is_edit_mode=is_edit_mode
        )

    context = {
        'form': form,
        'staff_profile': staff_profile,
        'step': 1,
        'is_edit_mode': is_edit_mode,
    }

    return render(request, 'registry/wizard_step1.html', context)


@login_required
def wizard_step2(request, staff_id):
    """Step 2: อัปโหลดรูปถ่าย"""
    staff_profile = get_object_or_404(StaffProfile, pk=staff_id)

    # Check permission
    if request.user.role == 'submitter' and staff_profile.department != request.user.department:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้')
        return redirect('registry:staff_list')

    # Get or create photo
    photo, created = Photo.objects.get_or_create(staff_profile=staff_profile)

    # Check if this is edit mode (photo already exists with cropped image)
    is_edit_mode = not created and photo.cropped_photo

    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            photo = form.save(commit=False)

            # บันทึกรูปต้นฉบับก่อน เพื่อให้ได้ path
            photo.uploaded_by = request.user
            photo.save()

            # Handle crop data
            crop_x = request.POST.get('crop_x')
            crop_y = request.POST.get('crop_y')
            crop_width = request.POST.get('crop_width')
            crop_height = request.POST.get('crop_height')

            if all([crop_x, crop_y, crop_width, crop_height]):
                # บันทึกข้อมูล crop
                photo.crop_data = {
                    'x': int(float(crop_x)),
                    'y': int(float(crop_y)),
                    'width': int(float(crop_width)),
                    'height': int(float(crop_height))
                }

                # Crop รูปภาพจริงๆ
                try:
                    # เปิดรูปต้นฉบับ (ตอนนี้มี path แล้ว)
                    original_image = Image.open(photo.original_photo.path)

                    # Crop ตามพิกัดที่กำหนด
                    cropped_image = original_image.crop((
                        int(float(crop_x)),
                        int(float(crop_y)),
                        int(float(crop_x)) + int(float(crop_width)),
                        int(float(crop_y)) + int(float(crop_height))
                    ))

                    # Resize เป็น 300x400 (อัตราส่วน 3:4)
                    cropped_image = cropped_image.resize((300, 400), Image.Resampling.LANCZOS)

                    # บันทึกรูปที่ crop แล้ว
                    # สร้างชื่อไฟล์ใหม่ เช่น photo-crop.jpg
                    original_filename = os.path.basename(photo.original_photo.name)
                    name_without_ext = os.path.splitext(original_filename)[0]
                    cropped_filename = f"{name_without_ext}-crop.jpg"
                    cropped_path = os.path.join(settings.MEDIA_ROOT, 'photos', 'cropped', cropped_filename)

                    # สร้างโฟลเดอร์ถ้ายังไม่มี
                    os.makedirs(os.path.dirname(cropped_path), exist_ok=True)

                    # บันทึกรูป
                    cropped_image.save(cropped_path, 'JPEG', quality=95)

                    # อัปเดต field cropped_photo
                    photo.cropped_photo = os.path.join('photos', 'cropped', cropped_filename)

                    # เก็บขนาดไฟล์
                    photo.file_size = os.path.getsize(cropped_path)
                    photo.width = 300
                    photo.height = 400

                    # Save อีกครั้งหลัง crop เสร็จ
                    photo.save()

                except Exception as e:
                    messages.error(request, f'เกิดข้อผิดพลาดในการ crop รูปภาพ: {str(e)}')
                    return redirect('registry:wizard_step2', staff_id=staff_profile.id)

            # Update badge request status
            badge_request, created = BadgeRequest.objects.get_or_create(
                staff_profile=staff_profile,
                defaults={'status': 'photo_uploaded', 'created_by': request.user}
            )
            if not created and badge_request.status == 'draft':
                badge_request.status = 'photo_uploaded'
                badge_request.save()

            messages.success(request, 'อัปโหลดและ Crop รูปถ่ายเรียบร้อยแล้ว')

            # ถ้าเป็นโหมดแก้ไข ให้กลับไปหน้ารายละเอียด
            if is_edit_mode:
                return redirect('registry:staff_detail', staff_id=staff_profile.id)

            # ถ้าเป็นการสร้างใหม่ ให้ไป step 3
            return redirect('registry:wizard_step3', staff_id=staff_profile.id)
    else:
        form = PhotoUploadForm(instance=photo)

    context = {
        'form': form,
        'staff_profile': staff_profile,
        'photo': photo,
        'step': 2,
        'is_edit_mode': is_edit_mode,
    }

    return render(request, 'registry/wizard_step2.html', context)


@login_required
def wizard_step3(request, staff_id):
    """Step 3: ตรวจสอบข้อมูลและส่งคำขอ"""
    staff_profile = get_object_or_404(StaffProfile, pk=staff_id)

    # Check permission
    if request.user.role == 'submitter' and staff_profile.department != request.user.department:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้')
        return redirect('registry:staff_list')

    # Get photo (ถ้าต้องการ)
    photo = None
    if staff_profile.badge_type.requires_photo():
        try:
            photo = Photo.objects.get(staff_profile=staff_profile)
        except Photo.DoesNotExist:
            request.session['validation_error'] = {
                'title': 'ไม่สามารถดำเนินการต่อได้',
                'message': 'ยังไม่ได้อัปโหลดรูปถ่าย',
                'details': 'กรุณาอัปโหลดและครอปรูปถ่ายก่อนดำเนินการต่อ',
                'action_url': f'/registry/wizard/step2/{staff_id}/',
                'action_text': 'อัปโหลดรูป'
            }
            return redirect('registry:wizard_step2', staff_id=staff_id)

    # Get or create badge request
    badge_request, created = BadgeRequest.objects.get_or_create(
        staff_profile=staff_profile,
        defaults={'status': 'ready_to_submit'}
    )

    if request.method == 'POST':
        action = request.POST.get('action')  # 'submit'

        if action == 'submit':
            # ตรวจสอบ Zone ก่อนส่งคำขอ
            if not staff_profile.zone:
                request.session['validation_error'] = {
                    'title': 'ไม่สามารถส่งคำขอได้',
                    'message': 'ยังไม่ได้ระบุพื้นที่/โซน',
                    'details': 'กรุณากลับไปที่ขั้นตอนที่ 1 เพื่อเลือกพื้นที่/โซนที่ปฏิบัติงาน',
                    'action_url': f'/registry/wizard/step1/{staff_id}/',
                    'action_text': 'ไปแก้ไข'
                }
                return redirect('registry:wizard_step3', staff_id=staff_id)

            # ส่งคำขอ - submitted
            from apps.approvals.models import ApprovalLog
            from django.utils import timezone

            previous_status = badge_request.status
            badge_request.status = 'submitted'
            badge_request.submitted_at = timezone.now()
            badge_request.save()

            # Create approval log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='submit',
                previous_status=previous_status,
                new_status='submitted',
                comment='ส่งคำขอจาก wizard',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )

            messages.success(request, f'ส่งคำขอของ {staff_profile.full_name} เรียบร้อยแล้ว รอการอนุมัติ')
            return redirect('registry:staff_list')
    else:
        pass

    # Get work dates
    from apps.settings_app.models import SystemSetting
    from .utils import format_thai_date_range

    work_start_date_setting = SystemSetting.objects.filter(key='work_start_date').first()
    work_end_date_setting = SystemSetting.objects.filter(key='work_end_date').first()

    work_dates_display = ''
    if work_start_date_setting and work_end_date_setting:
        work_dates_display = format_thai_date_range(
            work_start_date_setting.value,
            work_end_date_setting.value
        )

    context = {
        'staff_profile': staff_profile,
        'photo': photo,
        'badge_request': badge_request,
        'step': 3,
        'work_dates_display': work_dates_display,
    }

    return render(request, 'registry/wizard_step3.html', context)


@login_required
def wizard_submit(request, request_id):
    """ส่งคำขอเพื่อตรวจสอบ"""
    badge_request = get_object_or_404(BadgeRequest, pk=request_id)

    # Check permission
    if request.user.role == 'submitter' and badge_request.staff_profile.department != request.user.department:
        messages.error(request, 'คุณไม่มีสิทธิ์ส่งคำขอนี้')
        return redirect('registry:staff_list')

    # Check if ready to submit
    if badge_request.status not in ['ready_to_submit', 'rejected']:
        messages.warning(request, 'คำขอนี้ไม่สามารถส่งได้ในสถานะปัจจุบัน')
        return redirect('registry:staff_list')

    # Check if zone exists
    if not badge_request.staff_profile.zone:
        request.session['validation_error'] = {
            'title': 'ไม่สามารถส่งคำขอได้',
            'message': 'ยังไม่ได้ระบุพื้นที่/โซน',
            'details': 'กรุณาแก้ไขข้อมูลบุคลากรเพื่อเลือกพื้นที่/โซนที่ปฏิบัติงาน',
            'action_url': f'/registry/staff/{badge_request.staff_profile.id}/',
            'action_text': 'ไปแก้ไข'
        }
        return redirect('registry:staff_detail', staff_id=badge_request.staff_profile.id)

    if request.method == 'POST':
        from django.utils import timezone

        badge_request.status = 'submitted'
        badge_request.submitted_at = timezone.now()
        badge_request.save()

        messages.success(request, f'ส่งคำขอสำหรับ {badge_request.staff_profile.full_name} เรียบร้อยแล้ว')
        return redirect('registry:staff_list')

    context = {
        'badge_request': badge_request,
    }

    return render(request, 'registry/submit_confirm.html', context)


@login_required
def staff_detail(request, staff_id):
    """รายละเอียดบุคลากร"""
    from apps.settings_app.models import SystemSetting
    from .utils import format_thai_date_range

    staff_profile = get_object_or_404(StaffProfile, pk=staff_id)

    # Check permission
    if request.user.role == 'submitter' and staff_profile.department != request.user.department:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้')
        return redirect('registry:staff_list')

    # Get related data
    try:
        photo = Photo.objects.get(staff_profile=staff_profile)
    except Photo.DoesNotExist:
        photo = None

    try:
        badge_request = BadgeRequest.objects.get(staff_profile=staff_profile)
    except BadgeRequest.DoesNotExist:
        badge_request = None

    # Get work dates from SystemSetting
    work_start_date_setting = SystemSetting.objects.filter(key='work_start_date').first()
    work_end_date_setting = SystemSetting.objects.filter(key='work_end_date').first()

    work_dates_display = ''
    if work_start_date_setting and work_end_date_setting:
        work_dates_display = format_thai_date_range(
            work_start_date_setting.value,
            work_end_date_setting.value
        )

    context = {
        'staff_profile': staff_profile,
        'photo': photo,
        'badge_request': badge_request,
        'work_dates_display': work_dates_display,
    }

    return render(request, 'registry/staff_detail.html', context)


@login_required
def staff_delete(request, staff_id):
    """ลบบุคลากร"""
    staff_profile = get_object_or_404(StaffProfile, pk=staff_id)

    # Check permission
    if request.user.role == 'submitter' and staff_profile.department != request.user.department:
        messages.error(request, 'คุณไม่มีสิทธิ์ลบข้อมูลนี้')
        return redirect('registry:staff_list')

    # Check if badge request exists and status
    try:
        badge_request = BadgeRequest.objects.get(staff_profile=staff_profile)
        # ห้ามลบถ้าสถานะ submitted ขึ้นไป
        if badge_request.status in ['submitted', 'under_review', 'approved', 'badge_created', 'printed', 'completed']:
            messages.error(request, f'ไม่สามารถลบได้ เนื่องจากคำขออยู่ในสถานะ "{badge_request.get_status_display()}" แล้ว')
            return redirect('registry:staff_detail', staff_id=staff_id)
    except BadgeRequest.DoesNotExist:
        pass

    if request.method == 'POST':
        staff_name = staff_profile.full_name

        # ลบรูปภาพถ้ามี
        try:
            photo = Photo.objects.get(staff_profile=staff_profile)
            # ลบไฟล์จริงๆ
            if photo.original_photo:
                if os.path.exists(photo.original_photo.path):
                    os.remove(photo.original_photo.path)
            if photo.cropped_photo:
                if os.path.exists(photo.cropped_photo.path):
                    os.remove(photo.cropped_photo.path)
            photo.delete()
        except Photo.DoesNotExist:
            pass

        # ลบ BadgeRequest และข้อมูลที่เกี่ยวข้อง (cascade จะลบให้อัตโนมัติ)
        staff_profile.delete()

        messages.success(request, f'ลบข้อมูล {staff_name} เรียบร้อยแล้ว')
        return redirect('registry:staff_list')

    context = {
        'staff_profile': staff_profile,
    }

    return render(request, 'registry/staff_delete_confirm.html', context)


@login_required
def bulk_submit(request):
    """ส่งคำขอหลายรายการพร้อมกัน (สำหรับ Submitter)"""
    if request.method != 'POST':
        return redirect('registry:staff_list')

    staff_ids = request.POST.getlist('staff_ids')
    if not staff_ids:
        messages.error(request, 'กรุณาเลือกรายการที่ต้องการส่ง')
        return redirect('registry:staff_list')

    success_count = 0
    error_count = 0
    error_messages = []

    for staff_id in staff_ids:
        try:
            staff_profile = StaffProfile.objects.get(pk=staff_id)

            # Check permissions
            if request.user.role == 'submitter' and staff_profile.department != request.user.department:
                error_count += 1
                error_messages.append(f'{staff_profile.full_name}: ไม่มีสิทธิ์')
                continue

            # Get or create badge request
            badge_request, created = BadgeRequest.objects.get_or_create(
                staff_profile=staff_profile,
                defaults={
                    'status': 'ready_to_submit',
                    'created_by': request.user
                }
            )

            # Check if can submit
            if badge_request.status not in ['draft', 'photo_uploaded', 'ready_to_submit', 'rejected']:
                error_count += 1
                error_messages.append(f'{staff_profile.full_name}: สถานะไม่เหมาะสม ({badge_request.get_status_display()})')
                continue

            # Check if photo exists (เฉพาะบัตรที่ต้องการรูป)
            if staff_profile.badge_type.requires_photo():
                try:
                    photo = Photo.objects.get(staff_profile=staff_profile)
                    if not photo.cropped_photo:
                        error_count += 1
                        error_messages.append(f'{staff_profile.full_name}: ยังไม่มีรูปถ่าย')
                        continue
                except Photo.DoesNotExist:
                    error_count += 1
                    error_messages.append(f'{staff_profile.full_name}: ยังไม่มีรูปถ่าย')
                    continue

            # Check if zone exists
            if not staff_profile.zone:
                error_count += 1
                error_messages.append(f'{staff_profile.full_name}: ยังไม่ระบุพื้นที่/โซน')
                continue

            # Update status
            from apps.approvals.models import ApprovalLog
            from django.utils import timezone

            previous_status = badge_request.status
            badge_request.status = 'submitted'
            badge_request.submitted_at = timezone.now()
            badge_request.save()

            # Create approval log
            ApprovalLog.objects.create(
                badge_request=badge_request,
                action='submit',
                previous_status=previous_status,
                new_status='submitted',
                comment='ส่งคำขอเป็นกลุ่ม',
                performed_by=request.user,
                ip_address=get_client_ip(request)
            )

            success_count += 1

        except StaffProfile.DoesNotExist:
            error_count += 1

    # Store results in session for modal display
    if error_count > 0:
        request.session['bulk_submit_errors'] = {
            'success_count': success_count,
            'error_count': error_count,
            'error_messages': error_messages,
        }
    elif success_count > 0:
        messages.success(request, f'ส่งคำขอสำเร็จ {success_count} รายการ')

    return redirect('registry:staff_list')


def get_client_ip(request):
    """ดึง IP address ของ client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =====================
# Badge Type Management
# =====================

@login_required
@admin_required
def badge_type_list(request):
    """รายการประเภทบัตร"""
    badge_types = BadgeType.objects.all().order_by('name')

    # Search
    search = request.GET.get('search', '')
    if search:
        badge_types = badge_types.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(color__icontains=search)
        )

    context = {
        'badge_types': badge_types,
        'search': search,
    }

    return render(request, 'registry/settings/badge_type_list.html', context)


@login_required
@admin_required
def badge_type_edit(request, badge_type_id):
    """แก้ไขประเภทบัตร"""
    badge_type = get_object_or_404(BadgeType, pk=badge_type_id)

    if request.method == 'POST':
        badge_type.name = request.POST.get('name')
        badge_type.color_code = request.POST.get('color_code')
        badge_type.description = request.POST.get('description')
        badge_type.is_active = request.POST.get('is_active') == 'on'
        badge_type.save()

        messages.success(request, f'อัปเดตข้อมูล {badge_type.name} เรียบร้อยแล้ว')
        return redirect('registry:badge_type_list')

    context = {
        'badge_type': badge_type,
    }

    return render(request, 'registry/settings/badge_type_edit.html', context)


@login_required
@admin_required
def badge_type_delete(request, badge_type_id):
    """ลบประเภทบัตร"""
    badge_type = get_object_or_404(BadgeType, pk=badge_type_id)

    # Check if badge type is being used
    staff_count = StaffProfile.objects.filter(badge_type=badge_type).count()

    if request.method == 'POST':
        if staff_count > 0:
            messages.error(request, f'ไม่สามารถลบประเภทบัตรนี้ได้ เนื่องจากมีบุคลากร {staff_count} คนใช้งานอยู่')
            return redirect('registry:badge_type_list')

        badge_type_name = badge_type.name
        badge_type.delete()

        messages.success(request, f'ลบประเภทบัตร {badge_type_name} เรียบร้อยแล้ว')
        return redirect('registry:badge_type_list')

    context = {
        'badge_type': badge_type,
        'staff_count': staff_count,
    }

    return render(request, 'registry/settings/badge_type_delete_confirm.html', context)


# =====================
# Zone Management
# =====================

@login_required
@admin_required
def zone_list(request):
    """รายการโซนปฏิบัติงาน"""
    zones = Zone.objects.all().order_by('order', 'code')

    # Search
    search = request.GET.get('search', '')
    if search:
        zones = zones.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    context = {
        'zones': zones,
        'search': search,
    }

    return render(request, 'registry/settings/zone_list.html', context)


@login_required
@admin_required
def zone_create(request):
    """สร้างโซนใหม่"""
    if request.method == 'POST':
        zone = Zone()
        zone.code = request.POST.get('code')
        zone.name = request.POST.get('name')
        zone.description = request.POST.get('description', '')
        zone.order = request.POST.get('order', 0)
        zone.is_active = request.POST.get('is_active') == 'on'
        zone.save()

        messages.success(request, f'สร้างโซน {zone.code} - {zone.name} เรียบร้อยแล้ว')
        return redirect('registry:zone_list')

    # Get next order number
    last_zone = Zone.objects.order_by('-order').first()
    next_order = (last_zone.order + 1) if last_zone else 1

    context = {
        'next_order': next_order,
    }

    return render(request, 'registry/settings/zone_form.html', context)


@login_required
@admin_required
def zone_edit(request, zone_id):
    """แก้ไขโซน"""
    zone = get_object_or_404(Zone, pk=zone_id)

    if request.method == 'POST':
        zone.code = request.POST.get('code')
        zone.name = request.POST.get('name')
        zone.description = request.POST.get('description', '')
        zone.order = request.POST.get('order', 0)
        zone.is_active = request.POST.get('is_active') == 'on'
        zone.save()

        messages.success(request, f'อัปเดตข้อมูล {zone.code} - {zone.name} เรียบร้อยแล้ว')
        return redirect('registry:zone_list')

    context = {
        'zone': zone,
        'is_edit': True,
    }

    return render(request, 'registry/settings/zone_form.html', context)


@login_required
@admin_required
def zone_delete(request, zone_id):
    """ลบโซน"""
    zone = get_object_or_404(Zone, pk=zone_id)

    # Check if zone is being used
    staff_count = StaffProfile.objects.filter(zone=zone).count()

    if request.method == 'POST':
        if staff_count > 0:
            messages.error(request, f'ไม่สามารถลบโซนนี้ได้ เนื่องจากมีบุคลากร {staff_count} คนใช้งานอยู่')
            return redirect('registry:zone_list')

        zone_name = f"{zone.code} - {zone.name}"
        zone.delete()

        messages.success(request, f'ลบโซน {zone_name} เรียบร้อยแล้ว')
        return redirect('registry:zone_list')

    context = {
        'zone': zone,
        'staff_count': staff_count,
    }

    return render(request, 'registry/settings/zone_delete_confirm.html', context)


@login_required
@admin_required
def work_dates_settings(request):
    """จัดการวันที่ปฏิบัติงาน"""
    from apps.settings_app.models import SystemSetting
    from datetime import datetime
    from .utils import format_thai_date

    # Get current setting
    work_date_setting = SystemSetting.objects.filter(key='work_date').first()

    if request.method == 'POST':
        date_str = request.POST.get('work_date')

        # Validate date
        try:
            work_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Update or create setting
            if work_date_setting:
                work_date_setting.value = date_str
                work_date_setting.save()
            else:
                SystemSetting.objects.create(
                    key='work_date',
                    value=date_str,
                    setting_type='string',
                    description='วันที่ปฏิบัติงาน (รูปแบบ YYYY-MM-DD)'
                )

            messages.success(request, 'บันทึกวันที่ปฏิบัติงานเรียบร้อยแล้ว')
            return redirect('registry:work_dates_settings')

        except ValueError:
            messages.error(request, 'รูปแบบวันที่ไม่ถูกต้อง กรุณาระบุวันที่ในรูปแบบ YYYY-MM-DD')
            return redirect('registry:work_dates_settings')

    # Format date for display (Thai format - full)
    work_date_thai = format_thai_date(
        work_date_setting.value if work_date_setting else None
    )

    # Format date for display (Thai format - short)
    work_date_thai_short = format_thai_date(
        work_date_setting.value if work_date_setting else None,
        short=True
    )

    context = {
        'work_date': work_date_setting.value if work_date_setting else '',
        'work_date_thai': work_date_thai,
        'work_date_thai_short': work_date_thai_short,
    }

    return render(request, 'registry/settings/work_dates.html', context)


# ==================== Excel Import Views ====================

@login_required
def staff_import_upload(request):
    """หน้าอัปโหลดไฟล์ Excel สำหรับ import ข้อมูลบุคลากร"""
    from .forms import ExcelImportForm
    import os
    import tempfile

    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)

        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            badge_type = form.cleaned_data['badge_type']
            zone = form.cleaned_data['zone']

            # บันทึกไฟล์ชั่วคราว
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            for chunk in excel_file.chunks():
                temp_file.write(chunk)
            temp_file.close()

            try:
                # Parse Excel file
                from .utils import parse_excel_staff
                staff_data_list = parse_excel_staff(temp_file.name)

                # เก็บข้อมูลใน session
                request.session['import_data'] = staff_data_list
                request.session['import_badge_type_id'] = badge_type.id
                request.session['import_zone_id'] = zone.id if zone else None
                request.session['import_filename'] = excel_file.name

                # ลบไฟล์ชั่วคราว
                os.unlink(temp_file.name)

                # Redirect ไปหน้า preview
                return redirect('registry:staff_import_preview')

            except Exception as e:
                # ลบไฟล์ชั่วคราวในกรณีเกิด error
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

                messages.error(request, f'เกิดข้อผิดพลาดในการอ่านไฟล์ Excel: {str(e)}')
                return redirect('registry:staff_import_upload')
    else:
        form = ExcelImportForm()

    return render(request, 'registry/import/staff_import_upload.html', {'form': form})


@login_required
def staff_import_preview(request):
    """หน้า preview ข้อมูลก่อนนำเข้า"""
    from apps.badges.models import BadgeType

    # ดึงข้อมูลจาก session
    staff_data_list = request.session.get('import_data', [])
    badge_type_id = request.session.get('import_badge_type_id')
    zone_id = request.session.get('import_zone_id')
    filename = request.session.get('import_filename', '')

    if not staff_data_list or not badge_type_id:
        messages.warning(request, 'ไม่พบข้อมูลสำหรับนำเข้า กรุณาอัปโหลดไฟล์ใหม่')
        return redirect('registry:staff_import_upload')

    # ดึงข้อมูล badge_type และ zone
    badge_type = BadgeType.objects.get(id=badge_type_id)
    zone = Zone.objects.get(id=zone_id) if zone_id else None

    # ตรวจสอบข้อมูลซ้ำในฐานข้อมูล (เช็คจากบัตรประชาชน)
    for item in staff_data_list:
        national_id = item.get('national_id', '').strip()
        if national_id:
            # เช็คว่ามีในฐานข้อมูลหรือไม่
            existing = StaffProfile.objects.filter(national_id=national_id).first()
            if existing:
                item['is_duplicate'] = True
                item['duplicate_info'] = f'ซ้ำกับ: {existing.full_name}'
            else:
                item['is_duplicate'] = False
                item['duplicate_info'] = ''
        else:
            item['is_duplicate'] = False
            item['duplicate_info'] = ''

    # นับสถิติ
    total_count = len(staff_data_list)
    duplicate_count = sum(1 for item in staff_data_list if item.get('is_duplicate'))
    ready_count = total_count - duplicate_count

    context = {
        'staff_data_list': staff_data_list,
        'badge_type': badge_type,
        'zone': zone,
        'filename': filename,
        'total_count': total_count,
        'duplicate_count': duplicate_count,
        'ready_count': ready_count,
    }

    return render(request, 'registry/import/staff_import_preview.html', context)


@login_required
def staff_import_confirm(request):
    """บันทึกข้อมูลจาก Excel ลงฐานข้อมูล"""
    from django.db import transaction
    from apps.badges.models import BadgeType
    from apps.accounts.models import Department

    if request.method != 'POST':
        messages.warning(request, 'กรุณาใช้ฟอร์มสำหรับการนำเข้าข้อมูล')
        return redirect('registry:staff_import_upload')

    # ดึงข้อมูลจาก session
    staff_data_list = request.session.get('import_data', [])
    badge_type_id = request.session.get('import_badge_type_id')
    zone_id = request.session.get('import_zone_id')

    if not staff_data_list or not badge_type_id:
        messages.warning(request, 'ไม่พบข้อมูลสำหรับนำเข้า กรุณาอัปโหลดไฟล์ใหม่')
        return redirect('registry:staff_import_upload')

    # ดึงข้อมูล badge_type และ zone
    badge_type = BadgeType.objects.get(id=badge_type_id)
    zone = Zone.objects.get(id=zone_id) if zone_id else None

    # นับจำนวนข้อมูลที่จะ import
    success_count = 0
    skip_count = 0
    error_list = []

    try:
        with transaction.atomic():
            for item in staff_data_list:
                national_id = item.get('national_id', '').strip()

                # ข้ามข้อมูลซ้ำ
                if national_id and StaffProfile.objects.filter(national_id=national_id).exists():
                    skip_count += 1
                    continue

                try:
                    # หาหน่วยงานจากชื่อ (ถ้าไม่พบให้ใช้หน่วยงานของผู้ใช้)
                    department_name = item.get('department_name', '').strip()
                    department = None

                    if department_name:
                        department = Department.objects.filter(name__icontains=department_name).first()

                    if not department:
                        department = request.user.department

                    # สร้าง StaffProfile
                    staff_profile = StaffProfile.objects.create(
                        department=department,
                        title=item.get('title', ''),
                        first_name=item.get('first_name', ''),
                        last_name=item.get('last_name', ''),
                        national_id=national_id,
                        person_type=item.get('person_type', ''),
                        position=item.get('position', ''),
                        badge_type=badge_type,
                        zone=zone,
                        age=item.get('age'),
                        vaccine_dose_1=item.get('vaccine_dose_1', False),
                        vaccine_dose_2=item.get('vaccine_dose_2', False),
                        vaccine_dose_3=item.get('vaccine_dose_3', False),
                        vaccine_dose_4=item.get('vaccine_dose_4', False),
                        test_rt_pcr=item.get('test_rt_pcr', False),
                        test_atk=item.get('test_atk', False),
                        test_temperature=item.get('test_temperature', False),
                        notes=item.get('notes', ''),
                        created_by=request.user
                    )

                    # สร้าง BadgeRequest ในสถานะ draft
                    BadgeRequest.objects.create(
                        staff_profile=staff_profile,
                        status='draft',
                        created_by=request.user
                    )

                    success_count += 1

                except Exception as e:
                    error_list.append({
                        'row': item.get('row_number'),
                        'name': f"{item.get('title')}{item.get('first_name')} {item.get('last_name')}",
                        'error': str(e)
                    })

            # ล้างข้อมูลใน session
            request.session.pop('import_data', None)
            request.session.pop('import_badge_type_id', None)
            request.session.pop('import_zone_id', None)
            request.session.pop('import_filename', None)

    except Exception as e:
        messages.error(request, f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}')
        return redirect('registry:staff_import_preview')

    # แสดงผลลัพธ์
    if success_count > 0:
        messages.success(request, f'นำเข้าข้อมูลสำเร็จ {success_count} รายการ')

    if skip_count > 0:
        messages.info(request, f'ข้ามข้อมูลซ้ำ {skip_count} รายการ')

    if error_list:
        messages.warning(request, f'มีข้อผิดพลาด {len(error_list)} รายการ')

    # เก็บสถิติไว้แสดงในหน้า success
    request.session['import_result'] = {
        'success_count': success_count,
        'skip_count': skip_count,
        'error_count': len(error_list),
        'error_list': error_list
    }

    return redirect('registry:staff_import_success')


@login_required
def staff_import_success(request):
    """หน้าแสดงผลลัพธ์การ import"""
    import_result = request.session.get('import_result', {})

    if not import_result:
        messages.warning(request, 'ไม่พบข้อมูลผลลัพธ์การนำเข้า')
        return redirect('registry:staff_list')

    # ล้างข้อมูลใน session หลังแสดงผล
    request.session.pop('import_result', None)

    return render(request, 'registry/import/staff_import_success.html', {
        'import_result': import_result
    })

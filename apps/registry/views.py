from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from PIL import Image
import os
from django.conf import settings

from .models import StaffProfile, Photo, BadgeRequest
from .forms import StaffProfileForm, PhotoUploadForm, BadgeRequestReviewForm


@login_required
def staff_list(request):
    """รายการบุคลากร"""
    user = request.user

    # Filter by department for submitters
    if user.role == 'submitter':
        staff_profiles = StaffProfile.objects.filter(department=user.department).select_related(
            'badge_type', 'department'
        ).prefetch_related('badge_request')
    else:
        staff_profiles = StaffProfile.objects.all().select_related(
            'badge_type', 'department'
        ).prefetch_related('badge_request')

    # Search
    search = request.GET.get('search', '')
    if search:
        staff_profiles = staff_profiles.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(position__icontains=search)
        )

    context = {
        'staff_profiles': staff_profiles.order_by('-created_at'),
        'search': search,
    }

    return render(request, 'registry/staff_list.html', context)


@login_required
def wizard_step1(request, staff_id=None):
    """Step 1: ข้อมูลบุคลากร"""
    # Check if editing existing staff
    staff_profile = None
    if staff_id:
        staff_profile = get_object_or_404(StaffProfile, pk=staff_id)
        # Check permission
        if request.user.role == 'submitter' and staff_profile.department != request.user.department:
            messages.error(request, 'คุณไม่มีสิทธิ์แก้ไขข้อมูลนี้')
            return redirect('registry:staff_list')

    if request.method == 'POST':
        form = StaffProfileForm(request.POST, instance=staff_profile)
        if form.is_valid():
            staff = form.save(commit=False)
            # Set department from user if creating new
            if not staff_id:
                staff.department = request.user.department
                staff.created_by = request.user
            staff.save()

            messages.success(request, 'บันทึกข้อมูลบุคลากรเรียบร้อยแล้ว')
            return redirect('registry:wizard_step2', staff_id=staff.id)
    else:
        form = StaffProfileForm(instance=staff_profile)

    context = {
        'form': form,
        'staff_profile': staff_profile,
        'step': 1,
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

    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            photo = form.save(commit=False)

            # Handle crop data
            crop_x = request.POST.get('crop_x')
            crop_y = request.POST.get('crop_y')
            crop_width = request.POST.get('crop_width')
            crop_height = request.POST.get('crop_height')

            if all([crop_x, crop_y, crop_width, crop_height]):
                photo.crop_data = {
                    'x': int(float(crop_x)),
                    'y': int(float(crop_y)),
                    'width': int(float(crop_width)),
                    'height': int(float(crop_height))
                }

            photo.uploaded_by = request.user
            photo.save()

            # Update badge request status
            badge_request, created = BadgeRequest.objects.get_or_create(
                staff_profile=staff_profile,
                defaults={'status': 'photo_uploaded'}
            )
            if not created and badge_request.status == 'draft':
                badge_request.status = 'photo_uploaded'
                badge_request.save()

            messages.success(request, 'อัปโหลดรูปถ่ายเรียบร้อยแล้ว')
            return redirect('registry:wizard_step3', staff_id=staff_profile.id)
    else:
        form = PhotoUploadForm(instance=photo)

    context = {
        'form': form,
        'staff_profile': staff_profile,
        'photo': photo,
        'step': 2,
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

    # Get photo
    try:
        photo = Photo.objects.get(staff_profile=staff_profile)
    except Photo.DoesNotExist:
        messages.warning(request, 'กรุณาอัปโหลดรูปถ่ายก่อน')
        return redirect('registry:wizard_step2', staff_id=staff_id)

    # Get or create badge request
    badge_request, created = BadgeRequest.objects.get_or_create(
        staff_profile=staff_profile,
        defaults={'status': 'ready_to_submit'}
    )

    if request.method == 'POST':
        form = BadgeRequestReviewForm(request.POST)
        if form.is_valid():
            # Update status to ready_to_submit
            badge_request.status = 'ready_to_submit'
            badge_request.save()

            messages.success(request, 'ข้อมูลพร้อมส่งแล้ว คุณสามารถส่งคำขอได้จากหน้ารายการบุคลากร')
            return redirect('registry:staff_list')
    else:
        form = BadgeRequestReviewForm()

    context = {
        'form': form,
        'staff_profile': staff_profile,
        'photo': photo,
        'badge_request': badge_request,
        'step': 3,
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

    if request.method == 'POST':
        badge_request.status = 'submitted'
        badge_request.submitted_by = request.user
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

    context = {
        'staff_profile': staff_profile,
        'photo': photo,
        'badge_request': badge_request,
    }

    return render(request, 'registry/staff_detail.html', context)

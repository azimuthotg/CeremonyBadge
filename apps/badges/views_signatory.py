"""
Views for Badge Signatory Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from functools import wraps

from .models_signatory import BadgeSignatory


# Decorator for admin only
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (เฉพาะผู้ดูแลระบบ)')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def signatory_list(request):
    """รายการผู้เซ็นบัตร"""
    signatories = BadgeSignatory.objects.all().order_by('-is_active', 'rank', 'first_name')

    # Search
    search = request.GET.get('search', '')
    if search:
        signatories = signatories.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(rank__icontains=search) |
            Q(department__icontains=search)
        )

    context = {
        'signatories': signatories,
        'search': search,
    }

    return render(request, 'badges/signatory_list.html', context)


@login_required
@admin_required
def signatory_create(request):
    """สร้างผู้เซ็นบัตรใหม่"""
    if request.method == 'POST':
        try:
            signatory = BadgeSignatory.objects.create(
                rank=request.POST.get('rank', ''),
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                department=request.POST['department'],
                position=request.POST.get('position', ''),
                signature_image=request.FILES['signature_image'],
                is_active=request.POST.get('is_active') == 'on'
            )

            messages.success(request, f'เพิ่มผู้เซ็นบัตร {signatory.full_name} เรียบร้อยแล้ว')
            return redirect('badges:signatory_list')

        except KeyError as e:
            messages.error(request, f'กรุณากรอกข้อมูลให้ครบถ้วน: {str(e)}')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')

    return render(request, 'badges/signatory_form.html', {'signatory': None})


@login_required
@admin_required
def signatory_edit(request, signatory_id):
    """แก้ไขผู้เซ็นบัตร"""
    signatory = get_object_or_404(BadgeSignatory, pk=signatory_id)

    if request.method == 'POST':
        try:
            signatory.rank = request.POST.get('rank', '')
            signatory.first_name = request.POST['first_name']
            signatory.last_name = request.POST['last_name']
            signatory.department = request.POST['department']
            signatory.position = request.POST.get('position', '')
            signatory.is_active = request.POST.get('is_active') == 'on'

            # อัปโหลดรูปใหม่ (ถ้ามี)
            if 'signature_image' in request.FILES:
                signatory.signature_image = request.FILES['signature_image']

            signatory.save()

            messages.success(request, f'แก้ไขข้อมูล {signatory.full_name} เรียบร้อยแล้ว')
            return redirect('badges:signatory_list')

        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')

    context = {'signatory': signatory}
    return render(request, 'badges/signatory_form.html', context)


@login_required
@admin_required
def signatory_delete(request, signatory_id):
    """ลบผู้เซ็นบัตร"""
    if request.method != 'POST':
        return redirect('badges:signatory_list')

    signatory = get_object_or_404(BadgeSignatory, pk=signatory_id)

    # เก็บข้อมูลก่อนลบ
    name = signatory.full_name

    # ลบรูปลายเซ็น
    if signatory.signature_image:
        try:
            import os
            if os.path.exists(signatory.signature_image.path):
                os.remove(signatory.signature_image.path)
        except Exception as e:
            print(f"Error deleting signature image: {e}")

    # ลบผู้เซ็น
    signatory.delete()

    messages.success(request, f'ลบผู้เซ็นบัตร {name} เรียบร้อยแล้ว')
    return redirect('badges:signatory_list')

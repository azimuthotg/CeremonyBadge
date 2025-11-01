from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Div, Field
from crispy_forms.bootstrap import PrependedText
from .models import StaffProfile, Photo, BadgeRequest


class StaffProfileForm(forms.ModelForm):
    """ฟอร์มข้อมูลบุคลากร - Step 1"""

    class Meta:
        model = StaffProfile
        fields = [
            'title', 'first_name', 'last_name',
            'position', 'badge_type',
            'phone', 'email', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'ชื่อ'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'นามสกุล'}),
            'position': forms.TextInput(attrs={'placeholder': 'ตำแหน่ง'}),
            'phone': forms.TextInput(attrs={'placeholder': '0X-XXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'หมายเหตุ (ถ้ามี)'}),
        }
        labels = {
            'title': 'คำนำหน้า',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'position': 'ตำแหน่ง',
            'badge_type': 'ประเภทบัตร',
            'phone': 'เบอร์โทรศัพท์',
            'email': 'อีเมล',
            'notes': 'หมายเหตุ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3"><i class="bi bi-person-badge"></i> ข้อมูลส่วนตัว</h5>'),
            Row(
                Column('title', css_class='col-md-3'),
                Column('first_name', css_class='col-md-4'),
                Column('last_name', css_class='col-md-5'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-briefcase"></i> ข้อมูลการทำงาน</h5>'),
            Row(
                Column('position', css_class='col-md-6'),
                Column('badge_type', css_class='col-md-6'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-telephone"></i> ข้อมูลติดต่อ</h5>'),
            Row(
                Column('phone', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            'notes',
            Div(
                HTML('<button type="submit" class="btn btn-primary btn-lg"><i class="bi bi-arrow-right-circle"></i> ต่อไป: อัปโหลดรูปถ่าย</button>'),
                css_class='mt-4 d-grid'
            )
        )


class PhotoUploadForm(forms.ModelForm):
    """ฟอร์มอัปโหลดรูปถ่าย - Step 2"""

    class Meta:
        model = Photo
        fields = ['original_photo']
        labels = {
            'original_photo': 'เลือกรูปถ่าย',
        }
        widgets = {
            'original_photo': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('''
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    <strong>คำแนะนำ:</strong>
                    กรุณาเลือกรูปถ่ายที่ชัดเจน หน้าตรง พื้นหลังสีขาวหรือสีอ่อน ไฟล์ไม่เกิน 5MB
                </div>
            '''),
            'original_image',
            HTML('''
                <div id="preview-container" class="mt-3" style="display:none;">
                    <h6>ตัวอย่างรูปที่เลือก:</h6>
                    <div class="text-center">
                        <img id="image-preview" src="" style="max-width: 100%; max-height: 400px;">
                    </div>
                    <div id="crop-container" class="mt-3" style="display:none;">
                        <h6>ครอปรูปภาพ:</h6>
                        <div class="text-center">
                            <img id="image-to-crop" src="" style="max-width: 100%;">
                        </div>
                        <input type="hidden" id="crop_x" name="crop_x">
                        <input type="hidden" id="crop_y" name="crop_y">
                        <input type="hidden" id="crop_width" name="crop_width">
                        <input type="hidden" id="crop_height" name="crop_height">
                    </div>
                </div>
            '''),
            Div(
                HTML('''
                    <button type="button" id="btn-crop" class="btn btn-secondary btn-lg me-2" style="display:none;">
                        <i class="bi bi-crop"></i> ครอปรูป
                    </button>
                    <button type="submit" id="btn-submit" class="btn btn-primary btn-lg" disabled>
                        <i class="bi bi-arrow-right-circle"></i> ต่อไป: ตรวจสอบข้อมูล
                    </button>
                '''),
                css_class='mt-4 d-grid gap-2'
            )
        )


class BadgeRequestReviewForm(forms.Form):
    """ฟอร์มตรวจสอบข้อมูลก่อนส่ง - Step 3"""
    confirm = forms.BooleanField(
        required=True,
        label='ฉันยืนยันว่าข้อมูลทั้งหมดถูกต้องและครบถ้วน',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<div class="form-check mb-4">'),
            Field('confirm', css_class='form-check-input', template='bootstrap5/layout/checkboxselectmultiple.html'),
            HTML('</div>'),
            Div(
                HTML('''
                    <a href="#" onclick="history.back()" class="btn btn-outline-secondary btn-lg me-2">
                        <i class="bi bi-arrow-left-circle"></i> ย้อนกลับ
                    </a>
                    <button type="submit" class="btn btn-success btn-lg">
                        <i class="bi bi-check-circle"></i> ส่งคำขอ
                    </button>
                '''),
                css_class='d-grid gap-2 d-md-flex justify-content-md-end'
            )
        )

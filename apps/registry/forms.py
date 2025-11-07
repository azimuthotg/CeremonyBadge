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
            'department', 'title', 'first_name', 'last_name', 'national_id',
            'position', 'badge_type', 'zone',
            'age', 'vehicle_registration',
            'phone', 'email',
            'vaccine_dose_1', 'vaccine_dose_2', 'vaccine_dose_3', 'vaccine_dose_4',
            'test_rt_pcr', 'test_atk', 'test_temperature',
            'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'เช่น นาย, นาง, น.ส., พล.อ., พล.ต.'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'ชื่อ'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'นามสกุล'}),
            'national_id': forms.TextInput(attrs={'placeholder': 'X-XXXX-XXXXX-XX-X', 'maxlength': '13'}),
            'position': forms.TextInput(attrs={'placeholder': 'ตำแหน่ง/หน้าที่'}),
            'age': forms.NumberInput(attrs={'placeholder': 'อายุ', 'min': '0'}),
            'vehicle_registration': forms.TextInput(attrs={'placeholder': 'XX-XXXX กรุงเทพมหานคร'}),
            'phone': forms.TextInput(attrs={'placeholder': '0X-XXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'หมายเหตุ (ถ้ามี)'}),
        }
        labels = {
            'department': 'หน่วยงาน',
            'title': 'ยศ',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'national_id': 'บัตรประชาชน ๑๓ หลัก',
            'position': 'ตำแหน่ง/หน้าที่',
            'badge_type': 'ประเภทบัตร',
            'zone': 'พื้นที่/โซน',
            'age': 'อายุ',
            'vehicle_registration': 'ทะเบียนรถ',
            'phone': 'เบอร์โทรศัพท์',
            'email': 'อีเมล',
            'vaccine_dose_1': 'เข็ม ๑',
            'vaccine_dose_2': 'เข็ม ๒',
            'vaccine_dose_3': 'เข็ม ๓',
            'vaccine_dose_4': 'เข็ม ๔',
            'test_rt_pcr': 'RT-PCR',
            'test_atk': 'ATK',
            'test_temperature': 'วัดอุณหภูมิ',
            'notes': 'หมายเหตุ',
        }

    def __init__(self, *args, **kwargs):
        # Get user role and edit mode from kwargs if provided
        user_role = kwargs.pop('user_role', None)
        is_edit_mode = kwargs.pop('is_edit_mode', False)
        super().__init__(*args, **kwargs)

        # Hide department field for submitters (they use their own department)
        if user_role == 'submitter':
            self.fields['department'].widget = forms.HiddenInput()
            self.fields['department'].required = False

        # Customize zone field to show descriptions
        from .models import Zone
        self.fields['zone'].queryset = Zone.objects.filter(is_active=True)
        self.fields['zone'].label_from_instance = lambda obj: f"{obj.code} - {obj.name}"

        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Different layout for submitter vs officer/admin
        if user_role == 'submitter':
            layout_fields = [
                HTML('<h5 class="mb-3"><i class="bi bi-person-badge"></i> ข้อมูลส่วนตัว</h5>'),
                'department',  # Hidden field
                Row(
                    Column('title', css_class='col-md-2'),
                    Column('first_name', css_class='col-md-4'),
                    Column('last_name', css_class='col-md-6'),
                ),
                'national_id',
            ]
        else:
            layout_fields = [
                HTML('<h5 class="mb-3"><i class="bi bi-building"></i> หน่วยงาน</h5>'),
                'department',
                HTML('<h5 class="mb-3 mt-4"><i class="bi bi-person-badge"></i> ข้อมูลส่วนตัว</h5>'),
                Row(
                    Column('title', css_class='col-md-2'),
                    Column('first_name', css_class='col-md-4'),
                    Column('last_name', css_class='col-md-6'),
                ),
                'national_id',
            ]

        # Determine button text based on edit mode
        if is_edit_mode:
            submit_button = '<button type="submit" class="btn btn-success btn-lg"><i class="bi bi-check-circle"></i> บันทึก</button>'
        else:
            submit_button = '<button type="submit" class="btn btn-primary btn-lg"><i class="bi bi-arrow-right-circle"></i> ต่อไป: อัปโหลดรูปถ่าย</button>'

        layout_fields.extend([
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-briefcase"></i> ข้อมูลการทำงาน</h5>'),
            Row(
                Column('position', css_class='col-md-6'),
                Column('badge_type', css_class='col-md-6'),
            ),
            'zone',
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-person-circle"></i> ข้อมูลเพิ่มเติม</h5>'),
            Row(
                Column('age', css_class='col-md-6'),
                Column('vehicle_registration', css_class='col-md-6'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-telephone"></i> ข้อมูลติดต่อ</h5>'),
            Row(
                Column('phone', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-shield-check"></i> การรับวัคซีน</h5>'),
            Row(
                Column('vaccine_dose_1', css_class='col-md-3'),
                Column('vaccine_dose_2', css_class='col-md-3'),
                Column('vaccine_dose_3', css_class='col-md-3'),
                Column('vaccine_dose_4', css_class='col-md-3'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-clipboard-pulse"></i> การตรวจโควิดก่อนการปฏิบัติงาน</h5>'),
            Row(
                Column('test_rt_pcr', css_class='col-md-4'),
                Column('test_atk', css_class='col-md-4'),
                Column('test_temperature', css_class='col-md-4'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-chat-left-text"></i> หมายเหตุ</h5>'),
            'notes',
            Div(
                HTML(submit_button),
                css_class='mt-4 d-grid'
            )
        ])

        self.helper.layout = Layout(*layout_fields)

    def clean_national_id(self):
        """ตรวจสอบเลขบัตรประชาชน"""
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # Remove all non-digit characters
            national_id = ''.join(filter(str.isdigit, national_id))

            # Check length
            if len(national_id) != 13:
                raise forms.ValidationError('เลขบัตรประชาชนต้องมี 13 หลัก')

            return national_id
        return national_id


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

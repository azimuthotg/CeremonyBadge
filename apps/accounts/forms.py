from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Div
from .models import User, Department


class UserManagementForm(forms.ModelForm):
    """ฟอร์มจัดการผู้ใช้ (สำหรับ Admin)"""
    password1 = forms.CharField(
        label='รหัสผ่าน',
        widget=forms.PasswordInput(attrs={'placeholder': 'กรอกรหัสผ่าน'}),
        required=False,
        help_text='เว้นว่างไว้หากไม่ต้องการเปลี่ยนรหัสผ่าน'
    )
    password2 = forms.CharField(
        label='ยืนยันรหัสผ่าน',
        widget=forms.PasswordInput(attrs={'placeholder': 'กรอกรหัสผ่านอีกครั้ง'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active']
        labels = {
            'username': 'ชื่อผู้ใช้',
            'email': 'อีเมล',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'role': 'บทบาท',
            'department': 'หน่วยงาน',
            'is_active': 'เปิดใช้งาน',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'ชื่อ'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'นามสกุล'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_new = kwargs.pop('is_new', False)
        super().__init__(*args, **kwargs)

        # ถ้าเป็นการสร้างใหม่ ให้บังคับใส่รหัสผ่าน
        if self.is_new:
            self.fields['password1'].required = True
            self.fields['password2'].required = True
            self.fields['password1'].help_text = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3"><i class="bi bi-person-badge"></i> ข้อมูลส่วนตัว</h5>'),
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-shield-lock"></i> บทบาทและสิทธิ์</h5>'),
            Row(
                Column('role', css_class='col-md-6'),
                Column('department', css_class='col-md-6'),
            ),
            Row(
                Column('is_active', css_class='col-md-6'),
            ),
            HTML('<h5 class="mb-3 mt-4"><i class="bi bi-key"></i> รหัสผ่าน</h5>'),
            Row(
                Column('password1', css_class='col-md-6'),
                Column('password2', css_class='col-md-6'),
            ),
            Div(
                HTML('<a href="{% url \'accounts:user_list\' %}" class="btn btn-outline-secondary btn-lg me-2"><i class="bi bi-arrow-left"></i> ยกเลิก</a>'),
                HTML('<button type="submit" class="btn btn-primary btn-lg"><i class="bi bi-save"></i> บันทึก</button>'),
                css_class='mt-4 d-flex gap-2'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError('รหัสผ่านไม่ตรงกัน')
            if len(password1) < 8:
                raise forms.ValidationError('รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user


class DepartmentForm(forms.ModelForm):
    """ฟอร์มจัดการหน่วยงาน"""

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'order', 'is_active']
        labels = {
            'name': 'ชื่อหน่วยงาน',
            'code': 'รหัสหน่วยงาน',
            'description': 'รายละเอียด',
            'order': 'ลำดับการแสดงผล',
            'is_active': 'เปิดใช้งาน',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'ชื่อหน่วยงาน'}),
            'code': forms.TextInput(attrs={'placeholder': 'รหัสหน่วยงาน (ภาษาอังกฤษ)'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'รายละเอียดเพิ่มเติม (ถ้ามี)'}),
            'order': forms.NumberInput(attrs={'placeholder': 'เลขลำดับ (น้อยไปมาก)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3"><i class="bi bi-building"></i> ข้อมูลหน่วยงาน</h5>'),
            Row(
                Column('name', css_class='col-md-8'),
                Column('order', css_class='col-md-4'),
            ),
            Row(
                Column('code', css_class='col-md-12'),
            ),
            'description',
            Row(
                Column('is_active', css_class='col-md-6'),
            ),
            HTML('<div class="alert alert-info mt-3"><i class="bi bi-info-circle"></i> <strong>หมายเหตุ:</strong> ลำดับจะเรียงจากน้อยไปมาก (0, 1, 2, ...) หรือใช้ปุ่มลูกศรในหน้ารายการเพื่อจัดลำดับ</div>'),
            Div(
                HTML('<a href="{% url \'accounts:department_list\' %}" class="btn btn-outline-secondary btn-lg me-2"><i class="bi bi-arrow-left"></i> ยกเลิก</a>'),
                HTML('<button type="submit" class="btn btn-primary btn-lg"><i class="bi bi-save"></i> บันทึก</button>'),
                css_class='mt-4 d-flex gap-2'
            )
        )

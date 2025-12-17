# Troubleshooting - Print Manager PDF Generation

## 🐛 Error: "เกิดข้อผิดพลาด: Unexpected token '<',"

### สาเหตุ
JavaScript พยายาม parse HTML error page เป็น JSON

### วิธีแก้ไข

#### **ขั้นตอนที่ 1: ดู Error จริงๆ ใน Browser Console**

1. เปิด Browser DevTools:
   - **Chrome/Edge:** กด `F12` หรือ `Ctrl+Shift+I`
   - **Firefox:** กด `F12`
2. ไปที่แท็บ **Console**
3. ลองกดปุ่ม "Preview" หรือ "ดาวน์โหลด PDF" อีกครั้ง
4. ดู error message ใน Console

**ตัวอย่าง error ที่จะพบ:**
```
Server error response: <!DOCTYPE html>...
ModuleNotFoundError: No module named 'reportlab'
```

---

## 🔧 แก้ไขตามสาเหตุ

### **1. Missing Library - reportlab**

**Error:**
```
ModuleNotFoundError: No module named 'reportlab'
```

**วิธีแก้:**
```bash
# บน Production Server
cd C:\CeremonyBadge
Ceremony_env\Scripts\activate
pip install reportlab
```

**Linux:**
```bash
source Ceremony_env/bin/activate
pip install reportlab
```

---

### **2. Missing Library - Pillow**

**Error:**
```
ModuleNotFoundError: No module named 'PIL'
```

**วิธีแก้:**
```bash
pip install Pillow
```

---

### **3. File Permission Error**

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'C:\\CeremonyBadge\\media\\badges\\...'
```

**วิธีแก้ (Windows):**
```powershell
# ตั้งค่า permissions สำหรับโฟลเดอร์ media
icacls "C:\CeremonyBadge\media" /grant Users:(OI)(CI)F /T

# หรือ
Right-click media folder → Properties → Security → Edit
เพิ่ม Full Control สำหรับ NETWORK SERVICE และ IIS_IUSRS
```

**วิธีแก้ (Linux):**
```bash
sudo chown -R www-data:www-data media/
chmod -R 755 media/
```

---

### **4. Badge File Not Found**

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: '...badge_P-001.png'
```

**วิธีแก้:**

1. ตรวจสอบว่าบัตรมีไฟล์จริงหรือไม่:
```bash
ls -la media/badges/generated/
# หรือ Windows
dir media\badges\generated\
```

2. ถ้าไม่มี ให้สร้างบัตรใหม่:
   - ไปที่หน้า Badge Detail
   - คลิก "แก้ไขบัตร"
   - บันทึก (จะ regenerate บัตรใหม่)

---

### **5. CSRF Token Error**

**Error:**
```
403 Forbidden - CSRF verification failed
```

**วิธีแก้:**

1. **Clear browser cache** และ reload หน้าใหม่
2. **Logout และ Login ใหม่**
3. ตรวจสอบ `settings.py`:
```python
# ตรวจสอบว่ามี middleware นี้
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',
    ...
]
```

---

### **6. Memory Error (Large Number of Badges)**

**Error:**
```
MemoryError
```

**วิธีแก้:**

1. **ลดจำนวนบัตรที่เลือก** - เลือกไม่เกิน 8 ใบต่อครั้ง
2. **เพิ่ม memory limit** (Windows Server):
```powershell
# แก้ไข run_server.py หรือ service config
# เพิ่ม --timeout และ --threads
```

---

### **7. Template Error**

**Error:**
```
TemplateSyntaxError: Invalid block tag
```

**วิธีแก้:**

1. ตรวจสอบ template syntax
2. Run Django check:
```bash
python manage.py check --deploy
```

---

## 🧪 ทดสอบระบบ

### **Test 1: ตรวจสอบ Libraries**

```bash
source Ceremony_env/bin/activate
python -c "import reportlab; print('reportlab:', reportlab.Version)"
python -c "from PIL import Image; print('Pillow: OK')"
```

**ผลลัพธ์ที่ควรได้:**
```
reportlab: 4.0.7
Pillow: OK
```

---

### **Test 2: ทดสอบ PDF Generation ด้วย Django Shell**

```bash
python manage.py shell
```

```python
from apps.badges.models import Badge
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Test basic PDF generation
buffer = BytesIO()
pdf = canvas.Canvas(buffer, pagesize=A4)
pdf.drawString(100, 100, "Test PDF")
pdf.save()
buffer.seek(0)

print("✅ PDF generation works!")
print(f"PDF size: {len(buffer.getvalue())} bytes")
```

---

### **Test 3: ทดสอบ Badge File Access**

```bash
python manage.py shell
```

```python
from apps.badges.models import Badge
import os

# ดึงบัตร 1 อัน
badge = Badge.objects.first()
print(f"Badge: {badge.badge_number}")
print(f"File path: {badge.badge_file.path}")
print(f"File exists: {os.path.exists(badge.badge_file.path)}")

# ลองเปิดไฟล์
from PIL import Image
img = Image.open(badge.badge_file.path)
print(f"✅ Image size: {img.size}")
```

---

## 📋 Checklist สำหรับ Production

### **Pre-deployment:**
- [ ] ติดตั้ง reportlab: `pip install reportlab`
- [ ] ติดตั้ง Pillow: `pip install Pillow`
- [ ] สร้างโฟลเดอร์ media และ subfolders
- [ ] ตั้งค่า permissions สำหรับ media folder
- [ ] ทดสอบ PDF generation ด้วย shell

### **After deployment:**
- [ ] ทดสอบสร้างบัตร 1 ใบ
- [ ] ทดสอบ preview PDF
- [ ] ทดสอบ download PDF
- [ ] ตรวจสอบ browser console ไม่มี error
- [ ] ทดสอบกับ badges หลายสี

---

## 🚨 Error Messages อื่นๆ

### **"สามารถเลือกได้สูงสุด 8 บัตรเท่านั้น"**
**สาเหตุ:** เลือกบัตรเกิน 8 ใบ
**วิธีแก้:** ลดจำนวนบัตรในตะกร้า

### **"กรุณาเลือกบัตรที่ต้องการพิมพ์"**
**สาเหตุ:** ไม่ได้เลือกบัตรก่อนกด preview/download
**วิธีแก้:** เพิ่มบัตรลงตะกร้าก่อน

### **"ไม่พบบัตรที่เลือก"**
**สาเหตุ:** Badge ถูกลบหรือไม่มีอยู่จริง
**วิธีแก้:** Reload หน้าและเลือกบัตรใหม่

---

## 🛠️ วิธีรวบรวมข้อมูล Error สำหรับรายงาน

1. **เปิด Browser Console** (F12)
2. **Copy error message** ทั้งหมด
3. **ดู Django logs:**

**Windows:**
```powershell
# ถ้ารันด้วย run_server.py
# ดูใน terminal ที่รัน server

# ถ้ารันเป็น Windows Service
Get-EventLog -LogName Application -Source CeremonyBadge -Newest 50
```

**Linux:**
```bash
# Django development server
# ดูใน terminal

# Production (gunicorn/uwsgi)
tail -f /var/log/ceremonybadge/error.log
```

4. **ตรวจสอบ Python version และ libraries:**
```bash
python --version
pip list | grep -i reportlab
pip list | grep -i pillow
```

---

## 📞 ติดต่อสอบถาม

หากแก้ไขไม่ได้ กรุณาส่งข้อมูลต่อไปนี้:
1. Error message จาก Browser Console
2. Error logs จาก Django server
3. Python version: `python --version`
4. Installed packages: `pip list`
5. OS: Windows/Linux version
6. Screenshot ของ error

---

**อัพเดตล่าสุด:** 2025-01-17
**สำหรับ:** CeremonyBadge Print Manager

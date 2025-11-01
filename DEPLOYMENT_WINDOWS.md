# คู่มือติดตั้งและ Deploy ระบบบน Windows Server

## 📋 สารบัญ
1. [ข้อกำหนดระบบ](#ข้อกำหนดระบบ)
2. [ติดตั้ง Git และ Clone โปรเจกต์](#ติดตั้ง-git-และ-clone-โปรเจกต์)
3. [ติดตั้ง Python และ Dependencies](#ติดตั้ง-python-และ-dependencies)
4. [ติดตั้ง MySQL Database](#ติดตั้ง-mysql-database)
5. [ตั้งค่าระบบและ Environment](#ตั้งค่าระบบและ-environment)
6. [รัน Migrations และสร้างข้อมูลเริ่มต้น](#รัน-migrations-และสร้างข้อมูลเริ่มต้น)
7. [Deploy ด้วย Waitress (Production)](#deploy-ด้วย-waitress-production)
8. [ตั้งค่า Windows Service](#ตั้งค่า-windows-service)
9. [Troubleshooting](#troubleshooting)

---

## ข้อกำหนดระบบ

### ฮาร์ดแวร์ (แนะนำ)
- **CPU:** 4 cores หรือมากกว่า
- **RAM:** 8 GB หรือมากกว่า
- **Storage:** 50 GB หรือมากกว่า (สำหรับ database และ media files)

### ซอฟต์แวร์
- **OS:** Windows 10/11 หรือ Windows Server 2016/2019/2022
- **Python:** 3.10 หรือสูงกว่า
- **MySQL:** 8.0 หรือสูงกว่า
- **Git:** เวอร์ชันล่าสุด

---

## ติดตั้ง Git และ Clone โปรเจกต์

### 1. ติดตั้ง Git for Windows

#### ขั้นตอน:
1. ดาวน์โหลด Git จาก: https://git-scm.com/download/win
2. รันไฟล์ติดตั้ง `Git-x.xx.x-64-bit.exe`
3. ในหน้าจอติดตั้ง ใช้ค่า default ทั้งหมด (Next ไปเรื่อยๆ)
4. เมื่อติดตั้งเสร็จ เปิด **Git Bash** หรือ **PowerShell**

#### ตรวจสอบการติดตั้ง:
```bash
git --version
# ควรแสดง: git version 2.xx.x
```

### 2. Clone Repository

#### เปิด PowerShell หรือ Command Prompt:
```bash
# เข้าไปยังโฟลเดอร์ที่ต้องการเก็บโปรเจกต์
cd C:\Projects

# สร้างโฟลเดอร์ถ้ายังไม่มี
mkdir C:\Projects
cd C:\Projects

# Clone repository (แทน YOUR_TOKEN ด้วย Personal Access Token จริง)
git clone https://YOUR_TOKEN@github.com/azimuthotg/CeremonyBadge.git

# หรือ Clone ธรรมดา แล้วใส่ Username/Token ทีหลัง
git clone https://github.com/azimuthotg/CeremonyBadge.git

# เข้าไปในโฟลเดอร์โปรเจกต์
cd CeremonyBadge
```

#### ตรวจสอบไฟล์:
```bash
dir
# ควรเห็นไฟล์: manage.py, requirements.txt, apps/, templates/, etc.
```

---

## ติดตั้ง Python และ Dependencies

### 1. ติดตั้ง Python

#### ขั้นตอน:
1. ดาวน์โหลด Python 3.10+ จาก: https://www.python.org/downloads/windows/
2. รันไฟล์ติดตั้ง `python-3.xx.x-amd64.exe`
3. ⚠️ **สำคัญ:** ✅ เลือก "Add Python to PATH"
4. คลิก "Install Now"

#### ตรวจสอบการติดตั้ง:
```bash
python --version
# ควรแสดง: Python 3.10.x หรือสูงกว่า

pip --version
# ควรแสดง: pip xx.x.x
```

### 2. สร้าง Virtual Environment

```bash
# เข้าไปที่โฟลเดอร์โปรเจกต์
cd C:\Projects\CeremonyBadge

# สร้าง virtual environment
python -m venv venv

# เปิดใช้งาน virtual environment
venv\Scripts\activate

# หลังจากเปิดใช้งาน จะเห็น (venv) ข้างหน้า prompt
```

### 3. ติดตั้ง Dependencies

```bash
# ตรวจสอบว่าอยู่ใน virtual environment แล้ว (มี (venv) ข้างหน้า)

# อัพเกรด pip
python -m pip install --upgrade pip

# ติดตั้ง dependencies ทั้งหมด
pip install -r requirements.txt
```

### 4. ติดตั้ง Dependencies เพิ่มเติมสำหรับ Windows

```bash
# สำหรับ Production Server
pip install waitress

# สำหรับจัดการ Windows Service (ถ้าต้องการ)
pip install pywin32
```

---

## ติดตั้ง MySQL Database

### 1. ติดตั้ง MySQL Server

#### ขั้นตอน:
1. ดาวน์โหลด MySQL Installer จาก: https://dev.mysql.com/downloads/installer/
2. เลือก **mysql-installer-community-x.x.xx.msi** (Web)
3. รันไฟล์ติดตั้ง
4. เลือก **"Developer Default"** setup type
5. ติดตั้งตามขั้นตอน

#### การตั้งค่าระหว่างติดตั้ง:
- **Authentication Method:** Use Strong Password Encryption
- **Root Password:** ตั้งรหัสผ่านที่แข็งแรง (จดไว้!)
- **Windows Service:** ✅ เปิดใช้ (Start at System Startup)
- **Port:** 3306 (default)

### 2. สร้าง Database

#### เปิด MySQL Command Line Client:
```bash
# กด Start → พิมพ์ "MySQL Command Line Client"
# ใส่รหัสผ่าน root ที่ตั้งไว้
```

#### รันคำสั่ง SQL:
```sql
-- สร้าง Database
CREATE DATABASE CeremonyBadge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้าง User สำหรับระบบ (แนะนำ)
CREATE USER 'ceremony_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';

-- ให้สิทธิ์เข้าถึง Database
GRANT ALL PRIVILEGES ON CeremonyBadge.* TO 'ceremony_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- ตรวจสอบ
SHOW DATABASES;

-- ออกจาก MySQL
EXIT;
```

### 3. ทดสอบการเชื่อมต่อ

```bash
# ทดสอบเข้าด้วย user ที่สร้าง
mysql -u ceremony_user -p CeremonyBadge
# ใส่รหัสผ่าน: StrongPassword123!

# ถ้าเข้าได้ แสดงว่าสำเร็จ
EXIT;
```

---

## ตั้งค่าระบบและ Environment

### 1. สร้างไฟล์ Environment Variables

สร้างไฟล์ `.env` ในโฟลเดอร์ root (C:\Projects\CeremonyBadge):

```env
# Database Configuration
DB_NAME=CeremonyBadge
DB_USER=ceremony_user
DB_PASSWORD=StrongPassword123!
DB_HOST=localhost
DB_PORT=3306

# Django Secret Key
# สร้างใหม่ด้วยคำสั่ง: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=django-insecure-replace-this-with-real-secret-key

# Debug Mode (False ใน Production!)
DEBUG=False

# Allowed Hosts (เพิ่ม IP หรือ Domain ของ server)
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100,ceremonyserver.npu.ac.th
```

### 2. สร้าง Secret Key

```bash
# เปิด Python shell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copy output แล้วใส่ใน .env แทน SECRET_KEY
```

### 3. แก้ไฟล์ settings.py (ถ้าจำเป็น)

ไฟล์ `ceremony_badge/settings.py` ควรมีการอ่านค่าจาก .env:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='django-insecure-default')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='CeremonyBadge'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
    }
}
```

---

## รัน Migrations และสร้างข้อมูลเริ่มต้น

### 1. ตรวจสอบการเชื่อมต่อ Database

```bash
# เปิดใช้งาน virtual environment (ถ้ายังไม่ได้เปิด)
venv\Scripts\activate

# ทดสอบเชื่อมต่อ database
python manage.py check

# ควรแสดง: System check identified no issues
```

### 2. รัน Migrations

```bash
# รัน migrations เพื่อสร้างตารางใน database
python manage.py migrate

# ควรเห็นข้อความ:
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ... (เยอะๆ)
```

### 3. สร้าง Superuser

```bash
python manage.py createsuperuser

# กรอกข้อมูล:
# Username: admin
# Email: admin@npu.ac.th
# Password: ********** (ตั้งรหัสผ่านที่แข็งแรง)
# Password (again): **********
```

### 4. สร้างข้อมูลเริ่มต้น

```bash
# รันสคริปต์สร้างข้อมูลเริ่มต้น (หน่วยงาน + บัตร 4 สี)
python create_initial_data.py

# ควรเห็น:
# ✓ สร้างหน่วยงาน: มหาวิทยาลัยนครพนม
# ✓ สร้างประเภทบัตร: บัตรชมพู
# ✓ สร้างประเภทบัตร: บัตรแดง
# ✓ สร้างประเภทบัตร: บัตรเหลือง
# ✓ สร้างประเภทบัตร: บัตรเขียว
# ✅ สร้างข้อมูลเริ่มต้นเรียบร้อยแล้ว!
```

### 5. Collect Static Files (สำหรับ Production)

```bash
python manage.py collectstatic

# ตอบ: yes
```

### 6. ทดสอบรันระบบ

```bash
# รันเซิร์ฟเวอร์ทดสอบ
python manage.py runserver 0.0.0.0:8000

# เปิด browser ไปที่:
# http://localhost:8000/admin
# Login ด้วย superuser ที่สร้างไว้
```

---

## Deploy ด้วย Waitress (Production)

### 1. ติดตั้ง Waitress

```bash
pip install waitress
```

### 2. สร้างไฟล์ run_server.py

สร้างไฟล์ `run_server.py` ในโฟลเดอร์ root:

```python
"""
Production WSGI Server using Waitress
"""
import os
import sys

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ceremony_badge.settings')

from waitress import serve
from ceremony_badge.wsgi import application

if __name__ == '__main__':
    print('Starting Waitress WSGI server on 0.0.0.0:8000')
    print('Press Ctrl+C to stop')

    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=4,  # จำนวน worker threads
        url_scheme='http'
    )
```

### 3. รันด้วย Waitress

```bash
# เปิดใช้งาน virtual environment
venv\Scripts\activate

# รัน server
python run_server.py

# Server จะรันที่ http://0.0.0.0:8000
```

### 4. ทดสอบ

เปิด browser ไปที่:
- `http://localhost:8000/admin`
- `http://192.168.1.100:8000/admin` (เปลี่ยน IP เป็น IP จริงของ server)

---

## ตั้งค่า Windows Service

### วิธีที่ 1: ใช้ NSSM (Non-Sucking Service Manager) - แนะนำ

#### 1. ดาวน์โหลด NSSM
- ดาวน์โหลดจาก: https://nssm.cc/download
- แตกไฟล์ไปที่ `C:\nssm`

#### 2. ติดตั้ง Service

เปิด Command Prompt แบบ **Run as Administrator**:

```bash
# เข้าไปที่โฟลเดอร์ NSSM
cd C:\nssm\win64

# ติดตั้ง service
nssm install CeremonyBadge "C:\Projects\CeremonyBadge\venv\Scripts\python.exe" "C:\Projects\CeremonyBadge\run_server.py"

# ตั้งค่า service
nssm set CeremonyBadge AppDirectory "C:\Projects\CeremonyBadge"
nssm set CeremonyBadge DisplayName "NPU CeremonyBadge System"
nssm set CeremonyBadge Description "ระบบออกบัตรผู้ปฏิบัติงานพิธีพระราชทานปริญญาบัตร มหาวิทยาลัยนครพนม"
nssm set CeremonyBadge Start SERVICE_AUTO_START

# เริ่ม service
nssm start CeremonyBadge
```

#### 3. จัดการ Service

```bash
# ตรวจสอบสถานะ
nssm status CeremonyBadge

# หยุด service
nssm stop CeremonyBadge

# รีสตาร์ท service
nssm restart CeremonyBadge

# ลบ service
nssm remove CeremonyBadge confirm
```

### วิธีที่ 2: ใช้ Task Scheduler

#### 1. เปิด Task Scheduler
- กด `Win+R` พิมพ์ `taskschd.msc`

#### 2. สร้าง Task ใหม่
- คลิก **Create Task** (ขวาขวา)
- **General Tab:**
  - Name: `CeremonyBadge Server`
  - Run whether user is logged on or not: ✅
  - Run with highest privileges: ✅

#### 3. ตั้งค่า Trigger
- **Triggers Tab:** คลิก **New**
  - Begin the task: At startup
  - ✅ Enabled

#### 4. ตั้งค่า Action
- **Actions Tab:** คลิก **New**
  - Action: Start a program
  - Program/script: `C:\Projects\CeremonyBadge\venv\Scripts\python.exe`
  - Add arguments: `run_server.py`
  - Start in: `C:\Projects\CeremonyBadge`

#### 5. บันทึกและทดสอบ
- คลิก **OK**
- รีบูทเครื่องเพื่อทดสอบ

---

## Troubleshooting

### ปัญหา: MySQL Connection Error

**อาการ:** `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**แก้ไข:**
1. ตรวจสอบว่า MySQL Service กำลังทำงาน:
   ```bash
   # เปิด Services (Win+R → services.msc)
   # หา "MySQL80" → คลิกขวา → Start
   ```

2. ตรวจสอบ Firewall:
   ```bash
   # เปิด Windows Defender Firewall
   # อนุญาตให้ MySQL ใช้ port 3306
   ```

3. ตรวจสอบ `.env` ว่าข้อมูลถูกต้อง

### ปัญหา: Static Files ไม่แสดง

**อาการ:** CSS/JS ไม่ทำงาน

**แก้ไข:**
```bash
# Collect static files อีกครั้ง
python manage.py collectstatic --clear

# ตรวจสอบว่า STATIC_ROOT ใน settings.py ถูกต้อง
```

### ปัญหา: Port 8000 ถูกใช้แล้ว

**อาการ:** `Address already in use`

**แก้ไข:**
```bash
# หา process ที่ใช้ port 8000
netstat -ano | findstr :8000

# Kill process (เปลี่ยน PID ตามที่เจอ)
taskkill /PID xxxx /F

# หรือเปลี่ยนไปใช้ port อื่น
python manage.py runserver 0.0.0.0:8080
```

### ปัญหา: Import Error

**อาการ:** `ModuleNotFoundError: No module named 'xxx'`

**แก้ไข:**
```bash
# ตรวจสอบว่าอยู่ใน virtual environment
venv\Scripts\activate

# ติดตั้ง dependencies ใหม่
pip install -r requirements.txt
```

### ปัญหา: Permission Denied ตอน Collect Static

**อาการ:** Permission denied: 'staticfiles/...'

**แก้ไข:**
```bash
# รัน Command Prompt แบบ Administrator
# หรือเปลี่ยนสิทธิ์โฟลเดอร์
icacls "C:\Projects\CeremonyBadge\staticfiles" /grant Users:F /T
```

---

## 📝 Checklist การ Deploy

### Before Deployment
- [ ] Clone repository สำเร็จ
- [ ] ติดตั้ง Python และ dependencies
- [ ] ติดตั้ง MySQL และสร้าง database
- [ ] สร้างไฟล์ `.env` และตั้งค่าถูกต้อง
- [ ] รัน migrations สำเร็จ
- [ ] สร้าง superuser แล้ว
- [ ] รันสคริปต์ initial data สำเร็จ
- [ ] ทดสอบรัน development server สำเร็จ

### Production Deployment
- [ ] ตั้งค่า `DEBUG=False` ใน `.env`
- [ ] ตั้งค่า `ALLOWED_HOSTS` ถูกต้อง
- [ ] Collect static files สำเร็จ
- [ ] ทดสอบรัน Waitress server สำเร็จ
- [ ] ตั้งค่า Windows Service (NSSM หรือ Task Scheduler)
- [ ] ทดสอบเข้าระบบหลัง reboot

### Security
- [ ] เปลี่ยน SECRET_KEY เป็นค่าใหม่
- [ ] ตั้งรหัสผ่าน MySQL ที่แข็งแรง
- [ ] ตั้งรหัสผ่าน superuser ที่แข็งแรง
- [ ] ตรวจสอบว่าไฟล์ `.env` ไม่ถูก commit
- [ ] เปิด Firewall เฉพาะ port ที่จำเป็น

---

## 📞 Support & Contact

**Repository:** https://github.com/azimuthotg/CeremonyBadge
**Organization:** มหาวิทยาลัยนครพนม (NPU)
**Department:** สำนักวิทยบริการและเทคโนโลยีสารสนเทศ

---

**Last Updated:** 2025-11-01

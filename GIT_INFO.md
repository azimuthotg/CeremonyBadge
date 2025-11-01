# Git Repository Information - NPU CeremonyBadge

## 📦 Repository Details

**Repository URL:** https://github.com/azimuthotg/CeremonyBadge.git

**Personal Access Token (Classic):**
```
ghp_************************************
(โปรดเก็บ Token ไว้ในที่ปลอดภัย - อย่าแชร์หรือ commit ขึ้น GitHub)
```

**Branch:** main

**Owner:** azimuthotg

---

## 🔑 Git Configuration (Local)

```bash
git config user.name "NPU Developer"
git config user.email "developer@npu.ac.th"
```

---

## 📥 Clone Repository to Windows Server

### วิธีที่ 1: ใช้ Command Line (Git Bash หรือ PowerShell)

#### ขั้นตอนที่ 1: ติดตั้ง Git สำหรับ Windows
1. ดาวน์โหลด Git จาก: https://git-scm.com/download/win
2. ติดตั้งตามขั้นตอน (ใช้ค่า default ทั้งหมดได้)
3. เปิด **Git Bash** หรือ **PowerShell**

#### ขั้นตอนที่ 2: Clone Repository
```bash
# เข้าไปยังโฟลเดอร์ที่ต้องการ (เช่น C:\Projects)
cd C:\Projects

# Clone repository พร้อม authenticate ด้วย Personal Access Token
git clone https://YOUR_PERSONAL_ACCESS_TOKEN@github.com/azimuthotg/CeremonyBadge.git

# หรือ Clone ธรรมดา (จะขอ username/password ภายหลัง)
git clone https://github.com/azimuthotg/CeremonyBadge.git

# เข้าไปในโฟลเดอร์โปรเจกต์
cd CeremonyBadge
```

#### ขั้นตอนที่ 3: ตั้งค่า Git Config (ถ้าต้องการ)
```bash
git config user.name "NPU Developer"
git config user.email "developer@npu.ac.th"
```

---

### วิธีที่ 2: ใช้ GitHub Desktop (GUI)

#### ขั้นตอนที่ 1: ติดตั้ง GitHub Desktop
1. ดาวน์โหลดจาก: https://desktop.github.com/
2. ติดตั้งและเปิดโปรแกรม

#### ขั้นตอนที่ 2: Clone Repository
1. คลิก **File** → **Clone Repository**
2. เลือกแท็บ **URL**
3. ใส่ URL: `https://github.com/azimuthotg/CeremonyBadge.git`
4. เลือกโฟลเดอร์ที่ต้องการ (Local Path)
5. คลิก **Clone**

#### ขั้นตอนที่ 3: Authenticate ด้วย Personal Access Token
1. เมื่อถูกขอ Username และ Password:
   - **Username:** azimuthotg
   - **Password:** `YOUR_PERSONAL_ACCESS_TOKEN` (ใช้ Token แทนรหัสผ่าน)

---

## 🚀 ขั้นตอนหลัง Clone บน Windows Server

### 1. ติดตั้ง Python และ Virtual Environment

```bash
# สร้าง Virtual Environment
cd C:\Projects\CeremonyBadge
python -m venv venv

# เปิดใช้งาน Virtual Environment
venv\Scripts\activate

# ติดตั้ง Dependencies
pip install -r requirements.txt
```

### 2. ติดตั้ง MySQL และสร้าง Database

```sql
-- เปิด MySQL Command Line หรือ phpMyAdmin
CREATE DATABASE CeremonyBadge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้าง User สำหรับระบบ (ถ้าต้องการ)
CREATE USER 'ceremony_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON CeremonyBadge.* TO 'ceremony_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. ตั้งค่า Environment Variables (สร้างไฟล์ .env)

สร้างไฟล์ `.env` ในโฟลเดอร์ root:

```env
# Database Configuration
DB_NAME=CeremonyBadge
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Django Secret Key (สร้างใหม่ด้วย python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
SECRET_KEY=your-secret-key-here

# Debug Mode (ใช้ False ใน Production)
DEBUG=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip
```

### 4. รัน Migrations และสร้าง Superuser

```bash
# เปิดใช้งาน Virtual Environment
venv\Scripts\activate

# รัน Migrations
python manage.py migrate

# สร้าง Superuser
python manage.py createsuperuser

# สร้างข้อมูลเริ่มต้น
python create_initial_data.py

# Collect Static Files (สำหรับ Production)
python manage.py collectstatic
```

### 5. ทดสอบรันระบบ

```bash
# รันเซิร์ฟเวอร์ทดสอบ
python manage.py runserver 0.0.0.0:8000

# เปิด browser ไปที่:
# http://localhost:8000/admin
# http://localhost:8000/
```

---

## 🔄 Git Commands สำหรับพัฒนาต่อ

### Pull การเปลี่ยนแปลงล่าสุดจาก GitHub
```bash
git pull origin main
```

### ตรวจสอบสถานะไฟล์
```bash
git status
```

### Add ไฟล์ที่แก้ไข
```bash
# Add ทุกไฟล์
git add .

# หรือ Add เฉพาะไฟล์
git add path/to/file.py
```

### Commit การเปลี่ยนแปลง
```bash
git commit -m "commit message ของคุณ"
```

### Push ขึ้น GitHub
```bash
git push origin main
```

### ดู Log การ Commit
```bash
git log --oneline
```

### ดูความแตกต่างของไฟล์
```bash
git diff
```

### สร้าง Branch ใหม่ (สำหรับ Feature)
```bash
# สร้างและเปลี่ยนไปที่ branch ใหม่
git checkout -b feature/new-feature-name

# Push branch ใหม่ขึ้น GitHub
git push -u origin feature/new-feature-name

# กลับไปที่ main branch
git checkout main

# Merge feature branch เข้า main
git merge feature/new-feature-name
```

---

## 📝 Git Workflow แนะนำ

### สำหรับการพัฒนาทั่วไป:

```bash
# 1. Pull การเปลี่ยนแปลงล่าสุด
git pull origin main

# 2. แก้ไขโค้ด...

# 3. ตรวจสอบไฟล์ที่เปลี่ยน
git status

# 4. Add ไฟล์ที่ต้องการ commit
git add .

# 5. Commit พร้อม message
git commit -m "คำอธิบายการเปลี่ยนแปลง"

# 6. Push ขึ้น GitHub
git push origin main
```

### สำหรับการพัฒนา Feature ใหม่:

```bash
# 1. สร้าง branch ใหม่
git checkout -b feature/dashboard-enhancement

# 2. พัฒนา feature...

# 3. Commit การเปลี่ยนแปลง
git add .
git commit -m "Add dashboard enhancement"

# 4. Push feature branch
git push -u origin feature/dashboard-enhancement

# 5. สร้าง Pull Request บน GitHub (ถ้าต้องการ review)

# 6. Merge เข้า main
git checkout main
git merge feature/dashboard-enhancement
git push origin main
```

---

## ⚠️ Important Notes

### 1. Security
- ⚠️ **อย่าแชร์ Personal Access Token กับคนอื่น**
- ⚠️ **อย่า commit ไฟล์ .env ขึ้น GitHub**
- ⚠️ **ใช้ .gitignore เพื่อป้องกันไฟล์ sensitive**

### 2. Token Expiration
- Personal Access Token อาจหมดอายุ ตรวจสอบที่: https://github.com/settings/tokens
- ถ้าหมดอายุ ให้สร้าง token ใหม่และอัพเดทไฟล์นี้

### 3. Database
- ⚠️ **อย่า commit ไฟล์ database** (MySQL dumps, db.sqlite3)
- ใช้ migrations เพื่อจัดการ schema changes

### 4. Virtual Environment
- ⚠️ **อย่า commit โฟลเดอร์ venv/** (มี .gitignore แล้ว)
- ใช้ requirements.txt แทน

---

## 📞 Contact & Support

**Repository Owner:** azimuthotg
**GitHub:** https://github.com/azimuthotg/CeremonyBadge
**Organization:** มหาวิทยาลัยนครพนม (NPU)
**Department:** สำนักวิทยบริการและเทคโนโลยีสารสนเทศ

---

## 📚 Additional Resources

- **Git Documentation:** https://git-scm.com/doc
- **GitHub Guides:** https://guides.github.com/
- **Django Documentation:** https://docs.djangoproject.com/
- **Bootstrap 5 Docs:** https://getbootstrap.com/docs/5.0/

---

**Last Updated:** 2025-11-01
**Current Version:** Phase 1 (35% Complete)

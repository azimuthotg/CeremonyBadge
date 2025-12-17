# Database Configuration Guide - CeremonyBadge

## 📍 ที่อยู่การตั้งค่า Database

### **1. ไฟล์ .env (หลัก - ใช้ตัวนี้!)**

**ตำแหน่ง:** `/path/to/CeremonyBadge/.env`

```bash
# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=CeremonyBadge
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306
```

**สถานะ:** ✅ **อยู่ใน .gitignore** (ไม่ถูก commit - ปลอดภัย)

---

### **2. ไฟล์ settings.py (อ้างอิงค่าจาก .env)**

**ตำแหน่ง:** `ceremony_badge/settings.py` (line 98-111)

```python
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

**หมายเหตุ:** ❌ **ห้ามแก้ที่นี่!** ให้แก้ที่ไฟล์ `.env` แทน

---

### **3. ไฟล์ .env.example (Template สำหรับสร้าง .env ใหม่)**

**ตำแหน่ง:** `.env.example`

**วิธีใช้:**
```bash
# สร้าง .env จาก template
cp .env.example .env

# แก้ไขค่าใน .env
nano .env  # หรือใช้ text editor อื่น
```

---

## 🔧 วิธีตั้งค่า Database

### **ขั้นตอนที่ 1: สร้างไฟล์ .env (ถ้ายังไม่มี)**

```bash
# เข้าโฟลเดอร์โปรเจค
cd /path/to/CeremonyBadge

# สร้าง .env จาก template
cp .env.example .env
```

**บน Windows:**
```powershell
cd C:\CeremonyBadge
Copy-Item .env.example .env
```

---

### **ขั้นตอนที่ 2: แก้ไขค่าใน .env**

**Linux/Mac:**
```bash
nano .env
# หรือ
vim .env
# หรือ
code .env  # VS Code
```

**Windows:**
```powershell
notepad .env
# หรือ
code .env  # VS Code
```

---

### **ขั้นตอนที่ 3: กรอกข้อมูล Database**

**ตัวอย่างการตั้งค่า:**

#### **A. Development (ฐานข้อมูลในเครื่อง):**
```bash
DB_ENGINE=django.db.backends.mysql
DB_NAME=CeremonyBadge
DB_USER=root
DB_PASSWORD=your_mysql_root_password
DB_HOST=localhost
DB_PORT=3306
```

#### **B. Production (ฐานข้อมูล Remote):**
```bash
DB_ENGINE=django.db.backends.mysql
DB_NAME=CeremonyBadge_prod
DB_USER=ceremony_user
DB_PASSWORD=StrongPassword@2025!
DB_HOST=192.168.1.100
DB_PORT=3306
```

#### **C. Production (ใช้ socket - Linux):**
```bash
DB_ENGINE=django.db.backends.mysql
DB_NAME=CeremonyBadge
DB_USER=ceremony_user
DB_PASSWORD=StrongPassword@2025!
DB_HOST=/var/run/mysqld/mysqld.sock
DB_PORT=
```

---

## 🗄️ การสร้าง Database

### **วิธีที่ 1: ใช้ MySQL Command Line**

```bash
# เข้า MySQL
mysql -u root -p

# สร้างฐานข้อมูล
CREATE DATABASE CeremonyBadge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# สร้าง user และกำหนดสิทธิ์
CREATE USER 'ceremony_user'@'localhost' IDENTIFIED BY 'StrongPassword@2025!';
GRANT ALL PRIVILEGES ON CeremonyBadge.* TO 'ceremony_user'@'localhost';
FLUSH PRIVILEGES;

# ออกจาก MySQL
EXIT;
```

**Windows (ผ่าน Command Prompt):**
```cmd
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

---

### **วิธีที่ 2: ใช้ Script (แนะนำ)**

**มี script อยู่แล้วที่:** `scripts/create_production_db.py`

```bash
# Linux/Mac
source Ceremony_env/bin/activate
python scripts/create_production_db.py

# Windows
Ceremony_env\Scripts\activate
python scripts\create_production_db.py
```

---

### **วิธีที่ 3: ใช้ phpMyAdmin (ถ้ามี)**

1. เปิด phpMyAdmin (http://localhost/phpmyadmin)
2. Databases → Create database
3. ชื่อ: `CeremonyBadge`
4. Collation: `utf8mb4_unicode_ci`
5. Create

---

## 🔒 Security Best Practices

### **1. ใช้รหัสผ่านที่แข็งแกร่ง**

```bash
# ❌ ไม่ดี
DB_PASSWORD=123456
DB_PASSWORD=password

# ✅ ดี
DB_PASSWORD=C3r3m0ny@Bdg2025!XyZ
```

**สร้างรหัสผ่านแบบสุ่ม:**
```bash
# Linux/Mac
openssl rand -base64 32

# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### **2. สร้าง User เฉพาะสำหรับ Application**

**❌ ห้ามใช้:**
```bash
DB_USER=root  # อันตราย!
```

**✅ ควรใช้:**
```bash
DB_USER=ceremony_user  # User เฉพาะ
```

**วิธีสร้าง:**
```sql
-- สร้าง user
CREATE USER 'ceremony_user'@'localhost' IDENTIFIED BY 'StrongPassword@2025!';

-- ให้สิทธิ์เฉพาะฐานข้อมูล CeremonyBadge
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP
ON CeremonyBadge.* TO 'ceremony_user'@'localhost';

FLUSH PRIVILEGES;
```

---

### **3. จำกัด Remote Access (Production)**

**เปิดเฉพาะ localhost:**
```sql
CREATE USER 'ceremony_user'@'localhost' IDENTIFIED BY 'password';
```

**เปิดจาก IP เฉพาะ:**
```sql
CREATE USER 'ceremony_user'@'192.168.1.50' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON CeremonyBadge.* TO 'ceremony_user'@'192.168.1.50';
```

---

### **4. ป้องกันไฟล์ .env**

```bash
# ตั้งค่า permissions (Linux)
chmod 600 .env

# เฉพาะ owner อ่านและเขียนได้
ls -la .env
# ควรแสดง: -rw------- 1 user user
```

**Windows:**
- Right-click `.env` → Properties → Security
- ลบ permissions ของ Users ทั่วไป
- เหลือเฉพาะ Administrator และเจ้าของไฟล์

---

## 🔄 การสลับ Database (Development ↔ Production)

### **วิธีที่ 1: ใช้หลาย .env Files**

**สร้างไฟล์:**
```bash
.env.development   # สำหรับ development
.env.production    # สำหรับ production
```

**สลับ:**
```bash
# ใช้ development
cp .env.development .env

# ใช้ production
cp .env.production .env
```

---

### **วิธีที่ 2: ใช้ Scripts (มีอยู่แล้ว)**

**Linux/Mac:**
```bash
# สลับเป็น development
./use_development.sh

# สลับเป็น production
./use_production.sh
```

**Windows:**
```powershell
# สลับเป็น development
.\use_development.sh

# สลับเป็น production
.\use_production.sh
```

---

## 🧪 ทดสอบการเชื่อมต่อ Database

### **วิธีที่ 1: ใช้ Django Shell**

```bash
source Ceremony_env/bin/activate
python manage.py shell
```

```python
from django.db import connection
cursor = connection.cursor()
print("✅ Database connection successful!")
```

---

### **วิธีที่ 2: ใช้ Check Command**

```bash
python manage.py check --database default
```

---

### **วิธีที่ 3: ใช้ Script (แนะนำ)**

**มี script อยู่แล้วที่:** `scripts/check_database.py`

```bash
python scripts/check_database.py
```

**ผลลัพธ์:**
```
✅ Database connection successful!
Database: CeremonyBadge
Host: localhost:3306
User: ceremony_user
```

---

## 🚨 Troubleshooting

### **ปัญหา 1: Can't connect to MySQL server**

**สาเหตุ:**
- MySQL service ไม่ได้รัน
- HOST หรือ PORT ผิด

**แก้ไข:**
```bash
# Linux
sudo systemctl status mysql
sudo systemctl start mysql

# Windows
net start MySQL80

# ตรวจสอบ port
netstat -an | grep 3306  # Linux
netstat -an | findstr 3306  # Windows
```

---

### **ปัญหา 2: Access denied for user**

**สาเหตุ:**
- Username หรือ password ผิด
- User ไม่มีสิทธิ์

**แก้ไข:**
```sql
-- ตรวจสอบ user
SELECT user, host FROM mysql.user WHERE user = 'ceremony_user';

-- Reset password
ALTER USER 'ceremony_user'@'localhost' IDENTIFIED BY 'NewPassword@2025!';

-- ให้สิทธิ์ใหม่
GRANT ALL PRIVILEGES ON CeremonyBadge.* TO 'ceremony_user'@'localhost';
FLUSH PRIVILEGES;
```

---

### **ปัญหา 3: Unknown database 'CeremonyBadge'**

**สาเหตุ:**
- ยังไม่สร้างฐานข้อมูล

**แก้ไข:**
```sql
CREATE DATABASE CeremonyBadge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### **ปัญหา 4: django.core.exceptions.ImproperlyConfigured**

**สาเหตุ:**
- ไฟล์ .env ไม่มีหรือค่าผิด

**แก้ไข:**
```bash
# ตรวจสอบว่ามี .env หรือไม่
ls -la .env

# ตรวจสอบค่าใน .env
cat .env

# สร้างใหม่ถ้าไม่มี
cp .env.example .env
nano .env
```

---

## 📋 Checklist การตั้งค่า Database

### **Development:**
- [ ] สร้างไฟล์ `.env` จาก `.env.example`
- [ ] แก้ไขค่า `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- [ ] สร้าง database ใน MySQL
- [ ] สร้าง user และให้สิทธิ์
- [ ] ทดสอบการเชื่อมต่อ (`python manage.py check`)
- [ ] Run migrations (`python manage.py migrate`)

### **Production:**
- [ ] สร้าง `.env.production` พร้อมค่าจริง
- [ ] ใช้รหัสผ่านที่แข็งแกร่ง
- [ ] สร้าง user เฉพาะ (ไม่ใช่ root)
- [ ] จำกัด remote access
- [ ] ตั้งค่า permissions ไฟล์ `.env` (chmod 600)
- [ ] Backup database เป็นประจำ
- [ ] ทดสอบการเชื่อมต่อ
- [ ] Run migrations
- [ ] ตั้งค่า monitoring

---

## 📚 ไฟล์ที่เกี่ยวข้อง

| ไฟล์ | ตำแหน่ง | หมายเหตุ |
|------|---------|----------|
| **.env** | `/CeremonyBadge/.env` | ✅ ใช้ไฟล์นี้ (ไม่อยู่ใน Git) |
| **.env.example** | `/CeremonyBadge/.env.example` | Template สำหรับสร้าง .env |
| **settings.py** | `ceremony_badge/settings.py` | อ่านค่าจาก .env |
| **create_production_db.py** | `scripts/create_production_db.py` | Script สร้าง database |
| **check_database.py** | `scripts/check_database.py` | Script ทดสอบการเชื่อมต่อ |
| **use_production.sh** | `use_production.sh` | สลับเป็น production DB |
| **use_development.sh** | `use_development.sh` | สลับเป็น development DB |

---

## 🔗 Links

- [Django Database Documentation](https://docs.djangoproject.com/en/5.2/ref/settings/#databases)
- [MySQL 8.0 Documentation](https://dev.mysql.com/doc/)
- [python-decouple Documentation](https://pypi.org/project/python-decouple/)

---

**อัพเดตล่าสุด:** 2025-01-17
**สำหรับ:** CeremonyBadge v1.0

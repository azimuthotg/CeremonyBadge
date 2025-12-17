# 🗄️ คู่มือการจัดการฐานข้อมูล CeremonyBadge

## 📊 ฐานข้อมูลที่มี

ระบบมีฐานข้อมูล 2 ฐาน บน MySQL Server เดียวกัน (`110.78.83.101:3306`):

### 1. **CeremonyBadge** (Development)
- **ชื่อฐาน:** `ceremonybadge`
- **วัตถุประสงค์:** Development & Testing
- **DEBUG:** True
- **ไฟล์ .env:** `.env.development`

### 2. **CeremonyBadge_Production** (Production)
- **ชื่อฐาน:** `ceremonybadge_production`
- **วัตถุประสงค์:** Production (ใช้งานจริง)
- **DEBUG:** False
- **ไฟล์ .env:** `.env.production`

---

## 🔄 การสลับฐานข้อมูล

### **สลับไปใช้ Production:**
```bash
bash use_production.sh
```

### **สลับกลับไปใช้ Development:**
```bash
bash use_development.sh
```

### **ตรวจสอบฐานที่ใช้อยู่:**
```bash
source Ceremony_env/bin/activate
python scripts/check_database.py
```

---

## 📦 Scripts ที่มี

### **1. Backup ฐานข้อมูล**
```bash
source Ceremony_env/bin/activate
python scripts/backup_database.py
```
- สำรองข้อมูลเป็นไฟล์ JSON
- บันทึกที่: `backups/CeremonyBadge_backup_[timestamp].json`

### **2. สร้างฐาน Production ใหม่**
```bash
source Ceremony_env/bin/activate
python scripts/create_production_db.py
```
- สร้างฐาน `CeremonyBadge_Production` ใหม่
- ถ้ามีอยู่แล้วจะถามว่าต้องการลบและสร้างใหม่หรือไม่

### **3. Migrate Schema เข้า Production**
```bash
source Ceremony_env/bin/activate
python scripts/migrate_production.py
```
- Run Django migrations เข้าฐาน Production
- สร้างโครงสร้างตาราง

### **4. Import ข้อมูลเข้า Production**
```bash
source Ceremony_env/bin/activate
python scripts/import_to_production.py
```
- นำเข้าข้อมูลจาก backup ล่าสุด
- Import เข้าฐาน Production

### **5. ตรวจสอบฐานข้อมูล**
```bash
source Ceremony_env/bin/activate
python scripts/check_database.py
```
- แสดงข้อมูลการเชื่อมต่อปัจจุบัน
- แสดงจำนวน records
- แสดงว่าเป็น Development หรือ Production

---

## 🔐 ไฟล์ Environment

### **.env** (ปัจจุบัน)
- ไฟล์ที่ใช้งานอยู่ขณะนี้
- จะถูกสลับโดย scripts `use_production.sh` / `use_development.sh`

### **.env.development**
```ini
SECRET_KEY=tpw^d0j!bdb&vf3*e81vj6ch%3&fn16@^_rgrr0$uzlz*mupr=
DEBUG=True
DB_NAME=CeremonyBadge
```

### **.env.production**
```ini
SECRET_KEY=prod-8k$m9^@x7h#nq2w!v5p*e&j6d+f3s-a4g1c~z0y8u7t6r5e
DEBUG=False
DB_NAME=CeremonyBadge_Production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,110.78.83.101
```

---

## 📋 ขั้นตอนที่ทำไปแล้ว

✅ **1. Backup ฐานเดิม**
- สำรองฐาน `CeremonyBadge` เดิม
- ไฟล์: `backups/CeremonyBadge_backup_20251209_102459.json`
- ขนาด: 0.27 MB
- จำนวน objects: 617

✅ **2. สร้างฐาน Production**
- สร้างฐาน `CeremonyBadge_Production` สำเร็จ
- Character set: utf8mb4
- Collation: utf8mb4_unicode_ci

✅ **3. Migrate Schema**
- Run migrations เข้าฐาน Production สำเร็จ
- สร้าง 23 tables

✅ **4. Import ข้อมูล**
- Import ข้อมูลทั้งหมด 617 objects สำเร็จ
- Users: 3
- Departments: 26
- Staff: 97
- Requests: 97
- Badges: 12

✅ **5. สร้าง Scripts**
- `use_production.sh` - สลับไป Production
- `use_development.sh` - สลับกลับ Development
- `scripts/check_database.py` - ตรวจสอบฐาน

✅ **6. ทดสอบ**
- ทดสอบสลับฐานข้อมูลสำเร็จ
- ข้อมูลถูกต้องครบถ้วน

---

## 🎯 วิธีใช้งาน Production

### **1. สลับไปใช้ Production:**
```bash
# สลับฐาน
bash use_production.sh

# ตรวจสอบ
source Ceremony_env/bin/activate
python scripts/check_database.py
```

### **2. เริ่ม Server แบบ Production:**
```bash
# ตรวจสอบว่าสลับไป Production แล้ว
source Ceremony_env/bin/activate
python scripts/check_database.py

# Run server (ควรใช้ Waitress สำหรับ production)
python manage.py runserver 0.0.0.0:8000
```

### **3. ลบข้อมูลทดสอบ:**
เข้า Django Admin:
```
http://localhost:8000/admin/
```
- ลบ Users ที่เป็นทดสอบ
- ลบ Staff profiles ที่เป็นทดสอบ
- ลบ Badges ที่เป็นทดสอบ

---

## ⚠️ คำเตือนสำคัญ

### **Production Database:**
- ❌ **ห้าม** ลบข้อมูลโดยไม่ backup ก่อน
- ❌ **ห้าม** run migrations โดยตรงบนฐาน Production
- ✅ **ควร** backup ก่อนทำการแก้ไขใดๆ
- ✅ **ควร** ทดสอบบน Development ก่อนเสมอ

### **Environment Variables:**
- ⚠️ **ตรวจสอบ** ว่า DEBUG=False บน Production
- ⚠️ **อย่าลืม** สลับกลับไป Development หลังทำงานกับ Production
- ⚠️ **ระวัง** restart server หลังสลับฐาน

---

## 🔄 Backup & Restore

### **Backup Production:**
```bash
# สลับไป Production
bash use_production.sh

# Backup
source Ceremony_env/bin/activate
python scripts/backup_database.py

# สลับกลับ Development
bash use_development.sh
```

### **Restore Production:**
```bash
# สลับไป Production
bash use_production.sh

# Import จาก backup
source Ceremony_env/bin/activate
python scripts/import_to_production.py

# สลับกลับ Development
bash use_development.sh
```

---

## 📞 ข้อมูลการเชื่อมต่อ

### **MySQL Server:**
- **Host:** 110.78.83.101
- **Port:** 3306
- **User:** admin_e
- **Password:** 4128@card (⚠️ ควรเปลี่ยนเป็นรหัสที่แข็งแกร่งกว่านี้)

### **ฐานข้อมูล:**
1. `ceremonybadge` - Development
2. `ceremonybadge_production` - Production

---

## 📚 เอกสารเพิ่มเติม

- [README_NPU_CeremonyBadge.md](README_NPU_CeremonyBadge.md) - คู่มือการใช้งานระบบ
- [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md) - คู่มือการติดตั้ง
- [CLAUDE.md](CLAUDE.md) - คู่มือสำหรับ Claude Code

---

**อัพเดทล่าสุด:** 09 ธันวาคม 2568

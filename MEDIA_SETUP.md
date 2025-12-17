# Media Files Setup Guide

## สำหรับ Production Server

### 1. สร้างโฟลเดอร์ Media

```bash
cd /path/to/CeremonyBadge
mkdir -p media/badges/generated
mkdir -p media/photos/original
mkdir -p media/photos/cropped
mkdir -p media/signatures
mkdir -p media/files
```

### 2. ตั้งค่า Permissions

**สำหรับ Linux/Ubuntu:**

```bash
# เปลี่ยน owner เป็น web server user (ปรับตามระบบ)
sudo chown -R www-data:www-data media/

# หรือถ้าใช้ user อื่น
sudo chown -R your-user:your-user media/

# ตั้งค่า permissions
chmod -R 755 media/
```

**สำหรับ Windows Server:**

```powershell
# Right-click โฟลเดอร์ media
# Properties → Security → Edit
# เพิ่ม permissions:
# - NETWORK SERVICE: Full Control
# - IIS_IUSRS: Modify, Read & Execute, List folder contents
```

### 3. โครงสร้างโฟลเดอร์

```
media/
├── badges/
│   └── generated/          # บัตรที่สร้างแล้ว (badge_P-001.png)
├── photos/
│   ├── original/           # รูปต้นฉบับที่ upload
│   └── cropped/            # รูปที่ crop แล้ว (300x400)
├── signatures/             # ลายเซ็นอิเล็กทรอนิกส์ (PNG โปร่งใส)
└── files/                  # ไฟล์อื่นๆ (Excel import)
```

### 4. ตรวจสอบการตั้งค่า Django

**settings.py:**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**urls.py (สำหรับ development เท่านั้น):**
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 5. Web Server Configuration

**Nginx (Production):**
```nginx
server {
    ...

    # Media files
    location /media/ {
        alias /path/to/CeremonyBadge/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Static files
    location /static/ {
        alias /path/to/CeremonyBadge/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Apache (Production):**
```apache
<VirtualHost *:80>
    ...

    Alias /media/ /path/to/CeremonyBadge/media/
    Alias /static/ /path/to/CeremonyBadge/staticfiles/

    <Directory /path/to/CeremonyBadge/media>
        Require all granted
    </Directory>

    <Directory /path/to/CeremonyBadge/staticfiles>
        Require all granted
    </Directory>
</VirtualHost>
```

**IIS (Windows Server):**
1. เปิด IIS Manager
2. เลือก site → Add Virtual Directory
3. Alias: `media`, Path: `C:\path\to\CeremonyBadge\media`
4. Alias: `static`, Path: `C:\path\to\CeremonyBadge\staticfiles`

### 6. Backup Media Files

**สำคัญ!** โฟลเดอร์ media ไม่ได้อยู่ใน git

**ตั้งค่า backup ประจำวัน:**

```bash
#!/bin/bash
# backup_media.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/media"
SOURCE_DIR="/path/to/CeremonyBadge/media"

# สร้างโฟลเดอร์ backup
mkdir -p $BACKUP_DIR

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $SOURCE_DIR .

# ลบ backup เก่า (เก็บ 30 วัน)
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +30 -delete

echo "Media backup completed: media_$DATE.tar.gz"
```

**เพิ่มใน crontab:**
```bash
# Backup media ทุกวันเวลา 02:00
0 2 * * * /path/to/backup_media.sh
```

### 7. ขนาดไฟล์และ Quotas

**ตรวจสอบขนาด:**
```bash
du -sh media/
du -sh media/badges/
du -sh media/photos/
du -sh media/signatures/
```

**ตั้งค่า Upload Limits (Nginx):**
```nginx
client_max_body_size 10M;  # อนุญาตไฟล์สูงสุด 10MB
```

**ตั้งค่า Upload Limits (Django settings.py):**
```python
# Max upload size
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

### 8. Security

**ป้องกันการ execute scripts:**
```nginx
location ~* ^/media/.*\.(php|py|sh|exe)$ {
    deny all;
}
```

**ตรวจสอบ file types:**
```python
# Django settings.py
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_UPLOAD_SIZE = 5242880  # 5MB
```

### 9. Monitoring

**ตรวจสอบพื้นที่:**
```bash
# ตั้ง alert เมื่อ media ใหญ่เกิน 80%
df -h | grep media
```

**Log file uploads:**
```python
# ใน views.py
import logging
logger = logging.getLogger(__name__)

def upload_photo(request):
    logger.info(f"Photo uploaded by {request.user}: {file.name}")
```

### 10. การ Restore

**กรณี server ใหม่:**
```bash
# 1. สร้างโฟลเดอร์
mkdir -p media

# 2. Restore จาก backup
tar -xzf media_20250117.tar.gz -C media/

# 3. ตั้งค่า permissions
sudo chown -R www-data:www-data media/
chmod -R 755 media/
```

---

## Checklist สำหรับ Production

- [ ] สร้างโฟลเดอร์ media พร้อม subfolders
- [ ] ตั้งค่า permissions ถูกต้อง
- [ ] ตั้งค่า web server (Nginx/Apache/IIS) serve /media/
- [ ] ทดสอบ upload รูปภาพ
- [ ] ทดสอบ download/view รูปภาพ
- [ ] ตั้งค่า backup อัตโนมัติ
- [ ] ตั้งค่า monitoring พื้นที่
- [ ] ทดสอบ restore จาก backup

---

## Troubleshooting

**ปัญหา: ไม่สามารถ upload ไฟล์ได้**
```bash
# ตรวจสอบ permissions
ls -la media/photos/
# ควรเป็น: drwxr-xr-x ... www-data www-data

# แก้ไข
sudo chmod 755 media/photos/
```

**ปัญหา: รูปไม่แสดง (404)**
```bash
# ตรวจสอบไฟล์มีอยู่จริง
ls -la media/badges/generated/

# ตรวจสอบ web server config
# Nginx: sudo nginx -t
# Apache: sudo apachectl configtest
```

**ปัญหา: Permission Denied**
```bash
# ตรวจสอบ owner
ls -la media/
# แก้ไข
sudo chown -R www-data:www-data media/
```

---

**อัพเดตล่าสุด:** 2025-01-17
**สำหรับ:** CeremonyBadge Production Deployment

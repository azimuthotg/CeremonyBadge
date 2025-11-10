# 📋 Development Guidelines - NPU CeremonyBadge

**เอกสารแนวทางการพัฒนาระบบ**

---

## 🎯 UI/UX Guidelines

### 1. การยืนยัน (Confirmation)

**❌ ห้ามใช้:** `alert()` หรือ `confirm()` ของ JavaScript

**✅ ใช้:** Bootstrap Modal แทน

#### เหตุผล:
- UX ดีกว่า - สวยงาม, responsive, และควบคุมได้มากกว่า
- แสดงข้อมูลเพิ่มเติมได้มากกว่า
- รองรับ mobile และ tablet ได้ดี
- สอดคล้องกับ design system ของโปรเจค (Bootstrap 5)

#### ตัวอย่างการใช้งาน:

```html
<!-- ปุ่มเปิด Modal -->
<button type="button" class="btn btn-success" data-bs-toggle="modal" data-bs-target="#confirmModal">
    <i class="bi bi-check-circle"></i> ยืนยัน
</button>

<!-- Confirm Modal -->
<div class="modal fade" id="confirmModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h5 class="modal-title">
                    <i class="bi bi-check-circle"></i> ยืนยันการดำเนินการ
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    <strong>คำอธิบาย:</strong> รายละเอียดสิ่งที่จะเกิดขึ้น
                </div>
                <p>ข้อความยืนยัน</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <i class="bi bi-x-circle"></i> ยกเลิก
                </button>
                <form method="post" action="{% url 'your:action' %}" class="d-inline">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-success">
                        <i class="bi bi-check-circle"></i> ยืนยัน
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
```

#### สีของ Modal Header ตามการกระทำ:
- 🟢 `bg-success` - การยืนยัน, อนุมัติ, นำเข้า
- 🔴 `bg-danger` - การลบ, ปฏิเสธ
- 🟡 `bg-warning` - คำเตือน, ข้อมูลซ้ำ
- 🔵 `bg-primary` - ข้อมูลทั่วไป
- ⚫ `bg-secondary` - อื่นๆ

---

## 📝 อ้างอิง

- ดูตัวอย่างการใช้งาน Modal ที่ `templates/registry/import/staff_import_preview.html`
- Bootstrap 5 Modal Documentation: https://getbootstrap.com/docs/5.0/components/modal/

---

**อัปเดตล่าสุด:** 9 พฤศจิกายน 2568

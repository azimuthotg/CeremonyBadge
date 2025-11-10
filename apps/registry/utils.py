"""
Utility functions for registry app
"""
from datetime import datetime, date


def thai_month_name(month, short=False):
    """
    แปลงเลขเดือนเป็นชื่อเดือนภาษาไทย

    Args:
        month (int): เลขเดือน (1-12)
        short (bool): ใช้ชื่อย่อหรือไม่ (ธ.ค. vs ธันวาคม)

    Returns:
        str: ชื่อเดือนภาษาไทย
    """
    months_full = {
        1: 'มกราคม',
        2: 'กุมภาพันธ์',
        3: 'มีนาคม',
        4: 'เมษายน',
        5: 'พฤษภาคม',
        6: 'มิถุนายน',
        7: 'กรกฎาคม',
        8: 'สิงหาคม',
        9: 'กันยายน',
        10: 'ตุลาคม',
        11: 'พฤศจิกายน',
        12: 'ธันวาคม'
    }

    months_short = {
        1: 'ม.ค.',
        2: 'ก.พ.',
        3: 'มี.ค.',
        4: 'เม.ย.',
        5: 'พ.ค.',
        6: 'มิ.ย.',
        7: 'ก.ค.',
        8: 'ส.ค.',
        9: 'ก.ย.',
        10: 'ต.ค.',
        11: 'พ.ย.',
        12: 'ธ.ค.'
    }

    if short:
        return months_short.get(month, '')
    return months_full.get(month, '')


def arabic_to_thai_numerals(number):
    """
    แปลงเลขอารบิกเป็นเลขไทย

    Args:
        number: เลขอารบิก (int หรือ str)

    Returns:
        str: เลขไทย
    """
    thai_digits = ['๐', '๑', '๒', '๓', '๔', '๕', '๖', '๗', '๘', '๙']
    number_str = str(number)
    return ''.join(thai_digits[int(digit)] for digit in number_str)


def format_thai_date(date_value, short=False, use_thai_numerals=False):
    """
    แปลงวันที่เป็นรูปแบบไทย

    Args:
        date_value: วันที่ (date object, datetime object, หรือ string 'YYYY-MM-DD')
        short (bool): ใช้รูปแบบสั้นหรือไม่
        use_thai_numerals (bool): ใช้เลขไทยหรือไม่

    Returns:
        str: วันที่ภาษาไทย
        - แบบยาว: "24 ธันวาคม 2568" หรือ "๒๔ ธันวาคม ๒๕๖๘"
        - แบบสั้น: "24 ธ.ค. 2568" หรือ "๒๔ ธ.ค. ๒๕๖๘"

    Examples:
        >>> format_thai_date('2025-12-24')
        '24 ธันวาคม 2568'
        >>> format_thai_date('2025-12-24', short=True, use_thai_numerals=True)
        '๒๔ ธ.ค. ๒๕๖๘'
    """
    if not date_value:
        return ''

    # Convert string to date object if needed
    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        except ValueError:
            return ''

    # Convert datetime to date if needed
    if isinstance(date_value, datetime):
        date_value = date_value.date()

    if not isinstance(date_value, date):
        return ''

    # แปลงเป็น พ.ศ. (เพิ่ม 543 ปี)
    day = date_value.day
    month = thai_month_name(date_value.month, short=short)
    year = date_value.year + 543

    # แปลงเป็นเลขไทยถ้าต้องการ
    if use_thai_numerals:
        day = arabic_to_thai_numerals(day)
        year = arabic_to_thai_numerals(year)

    return f"{day} {month} {year}"


def format_thai_date_range(start_date, end_date, short=False):
    """
    แปลงช่วงวันที่เป็นรูปแบบไทย

    Args:
        start_date: วันที่เริ่มต้น
        end_date: วันที่สิ้นสุด
        short (bool): ใช้รูปแบบสั้นหรือไม่

    Returns:
        str: ช่วงวันที่ภาษาไทย

    Examples:
        >>> format_thai_date_range('2025-12-01', '2025-12-15')
        '1 ธันวาคม 2568 - 15 ธันวาคม 2568'
        >>> format_thai_date_range('2025-12-01', '2025-12-15', short=True)
        '1 ธ.ค. 2568 - 15 ธ.ค. 2568'
    """
    start_str = format_thai_date(start_date, short=short)
    end_str = format_thai_date(end_date, short=short)

    if start_str and end_str:
        return f"{start_str} - {end_str}"
    elif start_str:
        return start_str
    elif end_str:
        return end_str
    return ''


def parse_excel_staff(file_path):
    """
    Parse Excel file สำหรับ import ข้อมูลบุคลากร

    โครงสร้างไฟล์ Excel:
    - Row 1: หัวข้อหลัก (บัญชีรายชื่อเจ้าหน้าที่...)
    - Row 2: พื้นที่ (เช่น I, II, III)
    - Row 3: หัวคอลัมน์หลัก
    - Row 4: หัวคอลัมน์ย่อย (เข็ม 1, 2, 3, 4, RT-PCR, ATK, วัดอุณหภูมิ)
    - Row 5+: ข้อมูลจริง

    คอลัมน์ตามลำดับ:
    A: ลำดับ
    B: ยศ
    C: ชื่อ
    D: นามสกุล
    E: บัตรประชาชน 13 หลัก
    F: หน่วยงาน
    G: ประเภทบุคคล
    H: หน้าที่
    I: อายุ
    J: วัคซีนเข็ม 1
    K: วัคซีนเข็ม 2
    L: วัคซีนเข็ม 3
    M: วัคซีนเข็ม 4
    N: RT-PCR
    O: ATK
    P: วัดอุณหภูมิ
    Q: รูปภาพ (สำหรับชมพู/แดง - ว่างไว้) หรือ หมายเหตุ (สำหรับเหลือง/เขียว)

    Args:
        file_path (str): ที่อยู่ไฟล์ Excel

    Returns:
        list: รายการข้อมูลบุคลากรที่ parse แล้ว
    """
    import openpyxl

    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    # ข้ามแถวหัวข้อ (rows 1-4) เริ่มอ่านจาก row 5
    data_list = []

    for row_num, row in enumerate(ws.iter_rows(min_row=5, values_only=True), start=5):
        # ถ้าแถวว่างเปล่า (ลำดับเป็น None) ให้ข้ามไป
        if row[0] is None:
            continue

        # แยกข้อมูลตามคอลัมน์
        staff_data = {
            'row_number': row_num,  # เก็บหมายเลขแถวไว้สำหรับอ้างอิง
            'order': row[0],  # A: ลำดับ
            'title': str(row[1] or '').strip(),  # B: ยศ
            'first_name': str(row[2] or '').strip(),  # C: ชื่อ
            'last_name': str(row[3] or '').strip(),  # D: นามสกุล
            'national_id': str(row[4]).strip() if row[4] else '',  # E: บัตรประชาชน
            'department_name': str(row[5] or '').strip(),  # F: หน่วยงาน
            'person_type': str(row[6] or '').strip(),  # G: ประเภทบุคคล
            'position': str(row[7] or '').strip(),  # H: หน้าที่
            'age': int(row[8]) if row[8] and str(row[8]).strip() else None,  # I: อายุ

            # การรับวัคซีน (1 = True, None/0 = False)
            'vaccine_dose_1': bool(row[9] == 1),  # J: เข็ม 1
            'vaccine_dose_2': bool(row[10] == 1),  # K: เข็ม 2
            'vaccine_dose_3': bool(row[11] == 1),  # L: เข็ม 3
            'vaccine_dose_4': bool(row[12] == 1),  # M: เข็ม 4

            # การตรวจโควิดก่อนการปฏิบัติงาน (1 = True, None/0 = False)
            'test_rt_pcr': bool(row[13] == 1),  # N: RT-PCR
            'test_atk': bool(row[14] == 1),  # O: ATK
            'test_temperature': bool(row[15] == 1),  # P: วัดอุณหภูมิ

            # Q: รูปภาพ (สำหรับชมพู/แดง) หรือ หมายเหตุ (สำหรับเหลือง/เขียว)
            'notes': str(row[16] or '').strip() if len(row) > 16 else '',
        }

        data_list.append(staff_data)

    return data_list

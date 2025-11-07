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

"""Template filters for Thai date formatting"""
from django import template
from apps.registry.utils import format_thai_date

register = template.Library()


@register.filter(name='thai_date')
def thai_date(value, arg=''):
    """
    แปลงวันที่เป็นภาษาไทย (พ.ศ.)

    Usage:
        {{ date_value|thai_date }}           -> "24 ธันวาคม 2568"
        {{ date_value|thai_date:"short" }}   -> "24 ธ.ค. 68"
    """
    if not value:
        return ''

    short = (arg == 'short')
    return format_thai_date(value, short=short)


@register.filter(name='thai_datetime')
def thai_datetime(value, arg=''):
    """
    แปลงวันที่และเวลาเป็นภาษาไทย (พ.ศ.)

    Usage:
        {{ datetime_value|thai_datetime }}           -> "24 ธันวาคม 2568 14:30"
        {{ datetime_value|thai_datetime:"short" }}   -> "24 ธ.ค. 68 14:30"
    """
    if not value:
        return ''

    short = (arg == 'short')
    date_part = format_thai_date(value, short=short)

    # If short format, use 2-digit year
    if short and date_part:
        # Replace full year (2568) with 2-digit year (68)
        parts = date_part.split()
        if len(parts) == 3:
            year_full = parts[2]
            year_short = year_full[-2:]  # Last 2 digits
            date_part = f"{parts[0]} {parts[1]} {year_short}"

    time_part = value.strftime('%H:%M')

    return f"{date_part} {time_part}"

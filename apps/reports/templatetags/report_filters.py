from django import template

register = template.Library()

@register.filter
def percentage(value, total):
    """คำนวณเปอร์เซนต์"""
    try:
        value = float(value)
        total = float(total)
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """คูณตัวเลข"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """หารตัวเลข"""
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    """เข้าถึง dict โดยใช้ key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def sum_attr(list_of_dicts, attr):
    """รวมค่าของ attribute ใน list of dicts"""
    try:
        total = 0
        for item in list_of_dicts:
            if isinstance(item, dict):
                total += item.get(attr, 0)
            else:
                total += getattr(item, attr, 0)
        return total
    except (TypeError, AttributeError):
        return 0

@register.filter
def sum_badge_counts(list_of_dicts, color):
    """รวมค่าของ badge_counts[color] ใน list of dicts"""
    try:
        total = 0
        for item in list_of_dicts:
            badge_counts = item.get('badge_counts', {}) if isinstance(item, dict) else getattr(item, 'badge_counts', {})
            total += badge_counts.get(color, 0)
        return total
    except (TypeError, AttributeError):
        return 0

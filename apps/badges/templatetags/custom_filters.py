"""
Custom template filters for badges app
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key in template

    Usage:
        {{ badges_by_type|get_item:badge_type.color }}

    Args:
        dictionary: Dict object
        key: Key to access

    Returns:
        Value from dictionary or None if key doesn't exist
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

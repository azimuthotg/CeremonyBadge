"""
Template tags for badges app
"""
from django import template
from apps.badges.models_signatory import BadgeSignatory

register = template.Library()


@register.simple_tag
def get_active_signatories():
    """ดึงรายการผู้เซ็นที่ใช้งานอยู่"""
    return BadgeSignatory.objects.filter(is_active=True).order_by('rank', 'first_name')

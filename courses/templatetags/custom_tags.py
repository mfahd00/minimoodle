from django import template
from django.utils import timezone

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def days_until_expiry(enrollment):
    """Calculate days remaining until course access expires"""
    if not enrollment or not enrollment.course:
        return None
    
    expiry_date = enrollment.enrolled_at + timezone.timedelta(days=enrollment.course.duration_days)
    days_remaining = (expiry_date - timezone.now()).days
    
    return days_remaining

@register.filter
def days_until(due_date):
    """Calculate days remaining until a due date"""
    if not due_date:
        return None
    
    now = timezone.now()
    delta = due_date - now
    
    return delta.days

@register.filter
def abs_value(value):
    """Return the absolute value of a number"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value
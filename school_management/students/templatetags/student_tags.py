from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attribute(obj, attr):
    """Dynamic attribute access"""
    return getattr(obj, attr, None)

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply filter for calculations"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='behavior_avg')
def behavior_average(assessment):
    """Calculate average behavior score"""
    if not assessment:
        return 0
    return (assessment.participation + assessment.responsibility + 
            assessment.creativity + assessment.cooperation) / 4
from django import template
from decimal import Decimal, InvalidOperation
import math

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
    try:
        total = assessment.participation + assessment.responsibility + assessment.creativity + assessment.cooperation
        return total / 4
    except (TypeError, AttributeError):
        return 0

@register.filter(name='map_attribute')
def map_attribute(queryset, attr_name):
    """Extract a specific attribute from each object in a queryset"""
    return [getattr(obj, attr_name) for obj in queryset]

@register.filter(name='map_behavior_average')
def map_behavior_average(assessments):
    """Calculate average behavior score for each assessment"""
    return [behavior_average(assessment) for assessment in assessments]

@register.filter(name='map_bmi_values')
def map_bmi_values(health_records):
    """Extract BMI values from health records"""
    bmi_values = []
    for record in health_records:
        try:
            if record.bmi is not None and not math.isnan(float(record.bmi)):
                bmi_values.append(float(record.bmi))
            else:
                bmi_values.append(0)
        except (ValueError, TypeError, InvalidOperation):
            bmi_values.append(0)
    return bmi_values

@register.filter(name='safe_decimal')
def safe_decimal(value):
    """Safely convert decimal/float values to avoid InvalidOperation"""
    try:
        if value is None:
            return 0.0
        if isinstance(value, (Decimal, float, int)):
            if math.isnan(float(value)) or math.isinf(float(value)):
                return 0.0
            return float(value)
        # Handle string values that might be valid numbers
        if isinstance(value, str):
            return float(value.strip()) if value.strip() else 0.0
        return float(value)
    except (ValueError, TypeError, InvalidOperation):
        return 0.0

@register.filter(name='safe_floatformat')
def safe_floatformat(value, decimal_places=1):
    """Safely format decimal values"""
    try:
        safe_val = safe_decimal(value)
        return f"{safe_val:.{decimal_places}f}"
    except:
        return "0.0"
    

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def is_overdue(due_date):
    return due_date < timezone.now().date()

@register.filter
def sum_amount(queryset):
    """
    Template filter to sum amounts from a queryset of payments
    Usage: {{ invoice.payment_set.all|sum_amount }}
    """
    try:
        return sum(payment.amount for payment in queryset)
    except (TypeError, AttributeError):
        return 0


@register.filter
def subtract(value, arg):
    """
    Template filter to subtract two numbers
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import (
    FeeCategory, FeeItem, FeeStructure, FeeStructureItem, 
    Invoice, InvoiceLineItem, Payment
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'get_items_count', 'get_total_usage']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'is_active')
        }),
    )
    
    def get_items_count(self, obj):
        return obj.feeitem_set.count()
    get_items_count.short_description = 'Fee Items'
    
    def get_total_usage(self, obj):
        return FeeStructureItem.objects.filter(fee_item__category=obj).count()
    get_total_usage.short_description = 'Usage Count'


@admin.register(FeeItem)
class FeeItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_amount', 'is_optional', 'is_active', 'get_usage_count']
    list_filter = ['category', 'is_optional', 'is_active']
    search_fields = ['name', 'category__name', 'description']
    list_editable = ['is_optional', 'is_active']
    autocomplete_fields = ['category']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'description')
        }),
        ('Financial Details', {
            'fields': ('default_amount', 'is_optional')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_usage_count(self, obj):
        return obj.feestructureitem_set.count()
    get_usage_count.short_description = 'Used in Structures'


class FeeStructureItemInline(admin.TabularInline):
    model = FeeStructureItem
    extra = 1
    fields = ['fee_item', 'amount']
    autocomplete_fields = ['fee_item']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_level', 'term', 'get_total_amount', 'get_items_count', 'is_active', 'date_created']
    list_filter = ['class_level', 'term', 'is_active', 'date_created']
    search_fields = ['name', 'class_level__name']
    list_editable = ['is_active']
    readonly_fields = ['date_created', 'get_total_amount_display']
    inlines = [FeeStructureItemInline]
    
    fieldsets = (
        ('Structure Information', {
            'fields': ('name', 'class_level', 'term', 'is_active')
        }),
        ('Summary', {
            'fields': ('get_total_amount_display',),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'date_created'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_amount(self, obj):
        return "₦{:,.2f}".format(float(obj.total_amount))
    get_total_amount.short_description = 'Total Amount'
    
    def get_total_amount_display(self, obj):
        return "₦{:,.2f}".format(float(obj.total_amount))
    get_total_amount_display.short_description = 'Total Amount'
    
    def get_items_count(self, obj):
        return obj.feestructureitem_set.count()
    get_items_count.short_description = 'Items'


@admin.register(FeeStructureItem)
class FeeStructureItemAdmin(admin.ModelAdmin):
    list_display = ['fee_structure', 'fee_item', 'amount', 'get_category']
    list_filter = ['fee_item__category', 'fee_structure__class_level']
    search_fields = ['fee_structure__name', 'fee_item__name']
    autocomplete_fields = ['fee_structure', 'fee_item']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('fee_structure', 'fee_item', 'amount')
        }),
    )
    
    def get_category(self, obj):
        return obj.fee_item.category.name
    get_category.short_description = 'Category'


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0
    fields = ['fee_item', 'amount']
    readonly_fields = ['fee_item', 'amount']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    fields = ['amount', 'payment_method', 'transaction_reference', 'received_by']
    readonly_fields = ['payment_date']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'get_total_amount_display', 'get_paid_amount_display', 'get_balance_display', 'get_payment_status', 'issue_date', 'due_date']
    list_filter = ['is_paid', 'issue_date', 'due_date', 'fee_structure__class_level']
    search_fields = ['invoice_number', 'student__user__first_name', 'student__user__last_name', 'student__student_id']
    readonly_fields = ['issue_date', 'get_total_amount_display', 'get_paid_amount_display', 'get_balance_display']
    inlines = [InvoiceLineItemInline, PaymentInline]
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('student', 'fee_structure', 'invoice_number')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial Summary', {
            'fields': ('get_total_amount_display', 'get_paid_amount_display', 'get_balance_display', 'is_paid'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_amount(self, obj):
        """Return raw Decimal value for sorting/filtering."""
        return obj.total_amount
    get_total_amount.short_description = 'Total'
    
    def get_total_amount_display(self, obj):
        """Return formatted string for display."""
        return "₦{:,.2f}".format(float(obj.total_amount))
    get_total_amount_display.short_description = 'Invoice Total'
    
    def get_paid_amount(self, obj):
        """Return raw Decimal value for sorting/filtering."""
        return obj.payment_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    get_paid_amount.short_description = 'Paid'
    
    def get_paid_amount_display(self, obj):
        """Return formatted string for display."""
        paid = obj.payment_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return "₦{:,.2f}".format(float(paid))
    get_paid_amount_display.short_description = 'Amount Paid'
    
    def get_balance(self, obj):
        """Return raw Decimal value for sorting/filtering."""
        paid = obj.payment_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return obj.total_amount - paid
    get_balance.short_description = 'Balance'
    
    def get_balance_display(self, obj):
        """Return formatted HTML string for display."""
        paid = obj.payment_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        balance = obj.total_amount - paid
        color = 'green' if balance <= 0 else 'red'
        formatted_balance = "{:,.2f}".format(float(balance))
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{}</span>',
            color, formatted_balance
        )
    get_balance_display.short_description = 'Outstanding Balance'
    
    def get_payment_status(self, obj):
        """Return formatted HTML string for payment status."""
        paid = obj.payment_set.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        balance = obj.total_amount - paid
        
        if balance <= 0:
            color = 'green'
            status = 'Fully Paid'
        elif paid > 0:
            color = 'orange'
            status = 'Partially Paid'
        else:
            color = 'red'
            status = 'Unpaid'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_payment_status.short_description = 'Payment Status'

@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'fee_item', 'amount', 'get_category']
    list_filter = ['fee_item__category']
    search_fields = ['invoice__invoice_number', 'fee_item__name']
    autocomplete_fields = ['invoice', 'fee_item']
    
    def get_category(self, obj):
        return obj.fee_item.category.name
    get_category.short_description = 'Category'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_method', 'payment_date', 'transaction_reference', 'received_by']
    list_filter = ['payment_method', 'payment_date', 'received_by']
    search_fields = ['invoice__invoice_number', 'transaction_reference', 'invoice__student__user__first_name', 'invoice__student__user__last_name']
    readonly_fields = ['payment_date']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('invoice', 'amount', 'payment_method', 'transaction_reference')
        }),
        ('Processing Details', {
            'fields': ('payment_date', 'received_by', 'notes')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'invoice__student__user', 'received_by'
        )


# Custom Admin Site Actions
@admin.action(description='Mark invoices as paid')
def mark_as_paid(modeladmin, request, queryset):
    queryset.update(is_paid=True)

@admin.action(description='Mark invoices as unpaid')
def mark_as_unpaid(modeladmin, request, queryset):
    queryset.update(is_paid=False)

# Add actions to InvoiceAdmin
InvoiceAdmin.actions = [mark_as_paid, mark_as_unpaid]
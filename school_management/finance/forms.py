# finance/forms.py
from django import forms
from .models import (
    FeeCategory, FeeItem, FeeStructure,
    FeeStructureItem, Invoice, Payment
)
from django.forms import inlineformset_factory

class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# finance/forms.py
class FeeItemForm(forms.ModelForm):
    class Meta:
        model = FeeItem
        fields = ['name', 'category', 'description', 'is_active']  # Removed is_recurring
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'term', 'class_level', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].queryset = self.fields['term'].queryset.filter(is_current=True)

# Formset for FeeStructure items
FeeStructureItemFormSet = inlineformset_factory(
    FeeStructure,
    FeeStructureItem,
    fields=('fee_item', 'amount'),
    extra=1,
    can_delete=True
)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['student', 'fee_structure', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fee_structure'].queryset = FeeStructure.objects.filter(is_active=True)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'transaction_reference', 'notes']
        widgets = {
            'transaction_reference': forms.TextInput(attrs={'placeholder': 'Transaction ID/Reference'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter unpaid invoices or invoices with balance
        self.fields['invoice'].queryset = Invoice.objects.filter(is_paid=False)
        
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        invoice = self.cleaned_data.get('invoice')
        
        if invoice and amount:
            total_paid = sum(p.amount for p in invoice.payment_set.all())
            balance = invoice.total_amount - total_paid
            
            if amount > balance:
                raise forms.ValidationError(
                    f"Payment amount exceeds invoice balance. Maximum allowed: {balance}"
                )
        
        return amount
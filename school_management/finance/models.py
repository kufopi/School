from django.db import models
from academics.models import Class

class FeeCategory(models.Model):
    """Categories for different types of fees (tuition, development, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Fee Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class FeeItem(models.Model):
    """Individual components that make up a fee structure"""
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    default_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_optional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category__name', 'name']
    
    def __str__(self):
        return f"{self.category}: {self.name}"

class FeeStructure(models.Model):
    """Collection of fee items for a specific class and term"""
    name = models.CharField(max_length=100)  # e.g., "Primary 1 Fees 2023"
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE)
    term = models.ForeignKey('core.SchoolTerm', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_created = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('class_level', 'term')
        ordering = ['term__start_date', 'class_level__level']
    
    def __str__(self):
        return f"{self.name} - {self.class_level}"
    
    @property
    def total_amount(self):
        return sum(item.amount for item in self.feestructureitem_set.all())

class FeeStructureItem(models.Model):
    """Linking table between FeeStructure and FeeItem with specific amounts"""
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    fee_item = models.ForeignKey(FeeItem, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('fee_structure', 'fee_item')
        ordering = ['fee_item__category__name', 'fee_item__name']
    
    def __str__(self):
        return f"{self.fee_structure}: {self.fee_item} @ {self.amount}"

class Invoice(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT)
    invoice_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    notes = models.TextField(blank=True, null=True, help_text="Additional information about this invoice")
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.student}"
    
    @property
    def total_amount(self):
        return self.fee_structure.total_amount

class InvoiceLineItem(models.Model):
    """Breakdown of what the student is being charged for"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    fee_item = models.ForeignKey(FeeItem, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('invoice', 'fee_item')
    
    def __str__(self):
        return f"{self.invoice}: {self.fee_item}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Money'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    transaction_reference = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True, null=True)  # Add this line
    received_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice}"
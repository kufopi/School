# finance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from core.models import SchoolTerm
from academics.models import Class
from .models import (
    FeeCategory, FeeItem, FeeStructure, 
    FeeStructureItem, Invoice, InvoiceLineItem, Payment
)
from .forms import (
    FeeCategoryForm, FeeItemForm, FeeStructureForm,
    FeeStructureItemFormSet, InvoiceForm, PaymentForm
)

# Fee Category Views
class FeeCategoryListView(ListView):
    model = FeeCategory
    template_name = 'finance/fee_category_list.html'
    context_object_name = 'categories'

class FeeCategoryCreateView(CreateView):
    model = FeeCategory
    form_class = FeeCategoryForm
    template_name = 'finance/fee_category_form.html'
    success_url = reverse_lazy('fee_category_list')

class FeeCategoryUpdateView(UpdateView):
    model = FeeCategory
    form_class = FeeCategoryForm
    template_name = 'finance/fee_category_form.html'
    success_url = reverse_lazy('fee_category_list')

# Fee Item Views
class FeeItemListView(ListView):
    model = FeeItem
    template_name = 'finance/fee_item_list.html'
    context_object_name = 'fee_items'
    
    def get_queryset(self):
        return FeeItem.objects.filter(is_active=True)

class FeeItemCreateView(CreateView):
    model = FeeItem
    form_class = FeeItemForm
    template_name = 'finance/fee_item_form.html'
    success_url = reverse_lazy('fee_item_list')

class FeeItemUpdateView(UpdateView):
    model = FeeItem
    form_class = FeeItemForm
    template_name = 'finance/fee_item_form.html'
    success_url = reverse_lazy('fee_item_list')

# Fee Structure Views
class FeeStructureListView(ListView):
    model = FeeStructure
    template_name = 'finance/fee_structure_list.html'
    context_object_name = 'fee_structures'
    
    def get_queryset(self):
        return FeeStructure.objects.filter(is_active=True)

class FeeStructureCreateView(CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = FeeStructureItemFormSet(self.request.POST)
        else:
            context['formset'] = FeeStructureItemFormSet(queryset=FeeStructureItem.objects.none())
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('fee_structure_detail', kwargs={'pk': self.object.pk})

class FeeStructureDetailView(DetailView):
    model = FeeStructure
    template_name = 'finance/fee_structure_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.feestructureitem_set.all()
        context['total_amount'] = self.object.total_amount
        return context

class FeeStructureUpdateView(UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'finance/fee_structure_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = FeeStructureItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['formset'] = FeeStructureItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if formset.is_valid():
                formset.instance = self.object
                formset.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('fee_structure_detail', kwargs={'pk': self.object.pk})

# Invoice Views
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_terms'] = SchoolTerm.objects.filter(is_current=True)
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by student if student_id provided
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student__id=student_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'paid':
            queryset = queryset.filter(is_paid=True)
        elif status == 'unpaid':
            queryset = queryset.filter(is_paid=False)
        
        return queryset.select_related('student', 'fee_structure')

class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'
    
    def form_valid(self, form):
        with transaction.atomic():
            # Set invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            new_id = f"INV{int(last_invoice.id) + 1 if last_invoice else 1:05d}"
            form.instance.invoice_number = new_id
            
            # Set due date to 30 days from now
            form.instance.due_date = timezone.now() + timezone.timedelta(days=30)
            
            response = super().form_valid(form)
            
            # Create line items from fee structure
            fee_structure = form.cleaned_data['fee_structure']
            for item in fee_structure.feestructureitem_set.all():
                InvoiceLineItem.objects.create(
                    invoice=self.object,
                    fee_item=item.fee_item,
                    amount=item.amount
                )
            
            return response
    
    def get_success_url(self):
        return reverse_lazy('invoice_detail', kwargs={'pk': self.object.pk})

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_items'] = self.object.invoicelineitem_set.all()
        context['payments'] = self.object.payment_set.all()
        context['balance'] = self.object.total_amount - sum(
            p.amount for p in self.object.payment_set.all()
        )
        return context

# Payment Views
class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        invoice_id = self.kwargs.get('invoice_id')
        if invoice_id:
            initial['invoice'] = get_object_or_404(Invoice, pk=invoice_id)
        return initial
    
    def form_valid(self, form):
        invoice = form.cleaned_data['invoice']
        payment_amount = form.cleaned_data['amount']
        
        with transaction.atomic():
            # Save payment
            form.instance.received_by = self.request.user
            response = super().form_valid(form)
            
            # Update invoice status if fully paid
            total_paid = sum(
                p.amount for p in invoice.payment_set.all()
            ) + payment_amount
            
            if total_paid >= invoice.total_amount:
                invoice.is_paid = True
                invoice.save()
            
            return response
    
    def get_success_url(self):
        return reverse_lazy('invoice_detail', kwargs={'pk': self.object.invoice.pk})

# Report Views
def fee_structure_report(request, term_id=None):
    term = get_object_or_404(SchoolTerm, pk=term_id) if term_id else None
    classes = Class.objects.all()
    
    structures = FeeStructure.objects.filter(term=term) if term else FeeStructure.objects.none()
    
    # Calculate totals per class
    class_totals = []
    for class_obj in classes:
        structure = structures.filter(class_level=class_obj).first()
        if structure:
            class_totals.append({
                'class': class_obj,
                'total': structure.total_amount,
                'structure': structure
            })
    
    context = {
        'term': term,
        'class_totals': class_totals,
        'terms': SchoolTerm.objects.all()
    }
    return render(request, 'finance/fee_structure_report.html', context)

def generate_term_invoices(request, term_id):
    term = get_object_or_404(SchoolTerm, pk=term_id)
    students = term.session.student_set.filter(is_active=True)
    
    if request.method == 'POST':
        created_count = 0
        
        with transaction.atomic():
            for student in students:
                # Find applicable fee structure
                structure = FeeStructure.objects.filter(
                    class_level=student.current_class,
                    term=term,
                    is_active=True
                ).first()
                
                if structure and not Invoice.objects.filter(
                    student=student,
                    fee_structure=structure
                ).exists():
                    # Create invoice
                    last_invoice = Invoice.objects.order_by('-id').first()
                    new_id = f"INV{int(last_invoice.id) + 1 if last_invoice else 1:05d}"
                    
                    invoice = Invoice.objects.create(
                        student=student,
                        fee_structure=structure,
                        invoice_number=new_id,
                        due_date=timezone.now() + timezone.timedelta(days=30)
                    )
                    
                    # Create line items
                    for item in structure.feestructureitem_set.all():
                        InvoiceLineItem.objects.create(
                            invoice=invoice,
                            fee_item=item.fee_item,
                            amount=item.amount
                        )
                    
                    created_count += 1
        
        messages.success(request, f'Successfully generated {created_count} invoices for {term.name}')
        return redirect('invoice_list')
    
    context = {
        'term': term,
        'student_count': students.count(),
        'existing_invoices': Invoice.objects.filter(
            fee_structure__term=term
        ).count()
    }
    return render(request, 'finance/generate_term_invoices.html', context)

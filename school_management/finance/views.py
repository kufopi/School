# finance/views.py
from django.shortcuts import render, get_object_or_404, redirect
import requests
from django.conf import settings
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
            # Set invoice number - FIXED VERSION
            last_invoice = Invoice.objects.order_by('-id').first()
            
            if last_invoice and last_invoice.invoice_number.startswith('INV'):
                try:
                    # Extract numeric part from "INV00001" format
                    last_num = int(last_invoice.invoice_number[3:])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
                
            form.instance.invoice_number = f"INV{new_num:05d}"
            
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
            # Get the last invoice number once outside the loop
            last_invoice = Invoice.objects.order_by('-invoice_number').first()
            if last_invoice and last_invoice.invoice_number.startswith('INV'):
                try:
                    next_num = int(last_invoice.invoice_number[3:]) + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
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
                    # Create invoice with sequential numbering
                    invoice = Invoice.objects.create(
                        student=student,
                        fee_structure=structure,
                        invoice_number=f"INV{next_num:05d}",
                        due_date=timezone.now() + timezone.timedelta(days=30)
                    )
                    
                    next_num += 1  # Increment for next invoice
                    
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

# finance/views.py (add these imports)
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .payment_service import PaystackService
from django.views import View
from decimal import Decimal


# Add this to your views.py - Replace the existing InitiatePaymentView

class InitiatePaymentView(View):
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        email = request.POST.get('email')
        
        # Validate email
        if not email:
            messages.error(request, "Email address is required")
            return redirect('invoice_detail', pk=invoice_id)
        
        if invoice.is_paid:
            messages.warning(request, "Invoice is already paid")
            return redirect('invoice_detail', pk=invoice_id)
        
        # Initialize payment
        response = PaystackService.initialize_payment(request, invoice_id, email)
        
        # Check response status
        if response.get('status'):
            # Payment initialization successful
            authorization_url = response.get('data', {}).get('authorization_url')
            if authorization_url:
                return redirect(authorization_url)
            else:
                messages.error(request, "Payment URL not received from Paystack")
                return redirect('invoice_detail', pk=invoice_id)
        else:
            # Payment initialization failed
            error_message = response.get('message', 'Payment initialization failed')
            messages.error(request, f"Payment failed: {error_message}")
            return redirect('invoice_detail', pk=invoice_id)

# Replace the verify_payment function in views.py

@csrf_exempt
def verify_payment(request, invoice_id):
    """Verify payment callback from Paystack"""
    if request.method == 'GET':
        invoice = get_object_or_404(Invoice, id=invoice_id)
        reference = request.GET.get('reference')
        
        if not reference:
            messages.error(request, "Payment reference is missing")
            return redirect('invoice_detail', pk=invoice_id)
        
        try:
            # Verify the payment with Paystack
            response = PaystackService.verify_payment(reference)
            
            if response.get('status') and response.get('data', {}).get('status') == 'success':
                data = response['data']
                amount = Decimal(data['amount']) / 100  # Convert from kobo to naira
                
                # Check if this payment has already been recorded
                existing_payment = Payment.objects.filter(
                    transaction_reference=reference
                ).first()
                
                if existing_payment:
                    messages.info(request, "This payment has already been recorded")
                    return redirect('invoice_detail', pk=invoice_id)
                
                # Verify the amount matches (with small tolerance for rounding)
                if abs(amount - invoice.total_amount) > Decimal('0.01'):
                    messages.warning(
                        request, 
                        f"Payment amount (₦{amount}) doesn't match invoice amount (₦{invoice.total_amount})"
                    )
                
                # Create payment record
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=amount,
                    payment_method='card',
                    transaction_reference=reference,
                    received_by=request.user if request.user.is_authenticated else None,
                    notes=f"Paid via Paystack. Authorization: {data.get('authorization', {}).get('authorization_code', 'N/A')}"
                )
                
                # Update invoice status if fully paid
                total_paid = Payment.objects.filter(invoice=invoice).aggregate(
                    total=Sum('amount')
                )['total'] or Decimal('0')
                
                if total_paid >= invoice.total_amount:
                    invoice.is_paid = True
                    invoice.save()
                    messages.success(
                        request, 
                        f"Payment of ₦{amount} verified successfully! Invoice is now fully paid."
                    )
                else:
                    remaining = invoice.total_amount - total_paid
                    messages.success(
                        request, 
                        f"Payment of ₦{amount} verified successfully! Remaining balance: ₦{remaining}"
                    )
                
                return redirect('invoice_detail', pk=invoice_id)
            else:
                # Payment verification failed or payment not successful
                error_message = response.get('message', 'Payment verification failed')
                messages.error(request, f"Payment verification failed: {error_message}")
                return redirect('invoice_detail', pk=invoice_id)
                
        except Exception as e:
            print(f"Error in payment verification: {str(e)}")
            messages.error(request, f"An error occurred during payment verification: {str(e)}")
            return redirect('invoice_detail', pk=invoice_id)
    
    # If not GET request
    messages.error(request, "Invalid request method")
    return redirect('invoice_detail', pk=invoice_id)
    
# finance/views.py
@csrf_exempt
def paystack_webhook(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        event = payload.get('event')
        
        if event == 'charge.success':
            data = payload['data']
            reference = data['reference']
            
            # Verify the payment again for security
            verification = PaystackService.verify_payment(reference)
            
            if verification['status'] and verification['data']['status'] == 'success':
                try:
                    invoice = Invoice.objects.get(invoice_number=reference)
                    amount = Decimal(verification['data']['amount'])/100
                    
                    # Check if payment already exists
                    if not Payment.objects.filter(transaction_reference=reference).exists():
                        Payment.objects.create(
                            invoice=invoice,
                            amount=amount,
                            payment_method='card',
                            transaction_reference=reference,
                            received_by=None  # System recorded
                        )
                        
                        # Update invoice status
                        total_paid = sum(p.amount for p in invoice.payment_set.all())
                        if total_paid >= invoice.total_amount:
                            invoice.is_paid = True
                            invoice.save()
                            
                except Invoice.DoesNotExist:
                    pass
                
        return HttpResponse(status=200)
    return HttpResponse(status=400)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Invoice, Payment
from students.models import Student

@login_required
def student_finance_dashboard(request, student_id=None):
    # Get student (for students, use their own record; for staff, allow viewing specific student)
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        # Check permission - staff can view any, students can only view their own
        if request.user.user_type == 'student' and request.user.student != student:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
    else:
        if hasattr(request.user, 'student'):
            student = request.user.student
        else:
            # Staff viewing without specific student - redirect to finance home
            return redirect('invoice_list')
    
    # Get all invoices for the student
    # Get all invoices for the student with related data
    invoices = Invoice.objects.filter(student=student).select_related(
        'fee_structure', 'fee_structure__term'
    ).prefetch_related(
        'fee_structure__feestructureitem_set__fee_item__category'
    ).order_by('-issue_date')
    
    # Calculate totals
    total_outstanding = sum(
        invoice.total_amount - sum(p.amount for p in invoice.payment_set.all())
        for invoice in invoices if not invoice.is_paid
    )
    
    total_paid = sum(
        p.amount for invoice in invoices for p in invoice.payment_set.all()
    )
    
    # Find upcoming due invoice
    upcoming_due = None
    for invoice in invoices:
        if not invoice.is_paid and invoice.due_date > timezone.now().date():
            balance = invoice.total_amount - sum(p.amount for p in invoice.payment_set.all())
            if balance > 0:
                upcoming_due = {
                    'amount': balance,
                    'date': invoice.due_date
                }
                break
    
    # Get payment history
    payment_history = Payment.objects.filter(
        invoice__student=student
    ).select_related('invoice').order_by('-payment_date')[:20]
    
    # Add is_overdue property to each invoice
    for invoice in invoices:
        invoice.is_overdue = not invoice.is_paid and invoice.due_date < timezone.now().date()
        # Get fee structure items for this invoice
        invoice.fee_items = invoice.fee_structure.feestructureitem_set.all()
    
    context = {
        'student': student,
        'invoices': invoices,
        'payment_history': payment_history,
        'total_outstanding': total_outstanding,
        'total_paid': total_paid,
        'upcoming_due': upcoming_due,
    }
    
    return render(request, 'finance/student_finance_dashboard.html', context)

######################################################################################

# finance/accountant_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Invoice, Payment, FeeStructure, FeeItem, 
    FeeCategory, InvoiceLineItem
)
from students.models import Student
from core.models import SchoolTerm
from academics.models import Class
from .forms import PaymentForm


@login_required
def accountant_dashboard(request):
    """Main dashboard for accountant showing financial overview"""
    # Check if user is accountant/admin
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Get current term
    current_term = SchoolTerm.objects.filter(is_current=True).first()
    
    # Calculate totals
    total_invoiced = Invoice.objects.aggregate(
        total=Sum('fee_structure__feestructureitem__amount')
    )['total'] or 0
    
    total_collected = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_outstanding = total_invoiced - total_collected
    
    # Unpaid invoices count
    unpaid_count = Invoice.objects.filter(is_paid=False).count()
    
    # Overdue invoices
    overdue_invoices = Invoice.objects.filter(
        is_paid=False,
        due_date__lt=timezone.now().date()
    ).select_related('student', 'student__user')[:10]
    
    # Recent payments
    recent_payments = Payment.objects.select_related(
        'invoice', 'invoice__student', 'invoice__student__user'
    ).order_by('-payment_date')[:10]
    
    # Payment statistics for current month
    start_of_month = timezone.now().replace(day=1).date()
    monthly_payments = Payment.objects.filter(
        payment_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Class-wise collection summary
    class_summary = []
    for cls in Class.objects.all():
        students = Student.objects.filter(current_class=cls, is_active=True)
        invoices = Invoice.objects.filter(student__in=students)
        
        total_inv = sum(inv.total_amount for inv in invoices)
        total_paid = Payment.objects.filter(
            invoice__in=invoices
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        class_summary.append({
            'class': cls,
            'total_invoiced': total_inv,
            'total_collected': total_paid,
            'outstanding': total_inv - total_paid,
            'student_count': students.count()
        })
    
    context = {
        'current_term': current_term,
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'unpaid_count': unpaid_count,
        'overdue_invoices': overdue_invoices,
        'recent_payments': recent_payments,
        'monthly_payments': monthly_payments,
        'class_summary': class_summary,
    }
    
    return render(request, 'finance/accountant_dashboard.html', context)


@login_required
def record_payment(request, invoice_id=None):
    """Record a payment for an invoice"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.received_by = request.user
            payment.save()
            
            # Update invoice status
            inv = payment.invoice
            total_paid = Payment.objects.filter(invoice=inv).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            if total_paid >= inv.total_amount:
                inv.is_paid = True
                inv.save()
            
            messages.success(request, f"Payment of {payment.amount} recorded successfully.")
            return redirect('invoice_detail', pk=inv.pk)
    else:
        initial = {}
        if invoice:
            initial['invoice'] = invoice
            # Calculate remaining balance
            total_paid = Payment.objects.filter(invoice=invoice).aggregate(
                total=Sum('amount')
            )['total'] or 0
            initial['amount'] = invoice.total_amount - total_paid
        
        form = PaymentForm(initial=initial)
    
    context = {
        'form': form,
        'invoice': invoice,
    }
    
    return render(request, 'finance/record_payment.html', context)


@login_required
def payment_history(request):
    """View all payment history with filters"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    payments = Payment.objects.select_related(
        'invoice', 'invoice__student', 'invoice__student__user', 'received_by'
    ).order_by('-payment_date')
    
    # Filters
    payment_method = request.GET.get('payment_method')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    date_from = request.GET.get('date_from')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    student_id = request.GET.get('student_id')
    if student_id:
        payments = payments.filter(invoice__student_id=student_id)
    
    # Calculate totals
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments[:100],  # Limit to 100 records
        'total_amount': total_amount,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    
    return render(request, 'finance/payment_history.html', context)


@login_required
def outstanding_report(request):
    """Report showing all outstanding payments"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Get all unpaid invoices
    invoices = Invoice.objects.filter(is_paid=False).select_related(
        'student', 'student__user', 'student__current_class', 'fee_structure'
    ).order_by('due_date')
    
    # Calculate balances for each invoice
    invoice_data = []
    total_outstanding = 0
    
    for invoice in invoices:
        paid_amount = Payment.objects.filter(invoice=invoice).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        balance = invoice.total_amount - paid_amount
        
        if balance > 0:
            invoice_data.append({
                'invoice': invoice,
                'paid_amount': paid_amount,
                'balance': balance,
                'is_overdue': invoice.due_date < timezone.now().date()
            })
            total_outstanding += balance
    
    # Filter by class if requested
    class_id = request.GET.get('class_id')
    if class_id:
        invoice_data = [
            item for item in invoice_data 
            if item['invoice'].student.current_class_id == int(class_id)
        ]
    
    # Sort by overdue first
    invoice_data.sort(key=lambda x: (not x['is_overdue'], x['invoice'].due_date))
    
    context = {
        'invoice_data': invoice_data,
        'total_outstanding': total_outstanding,
        'classes': Class.objects.all(),
    }
    
    return render(request, 'finance/outstanding_report.html', context)


@login_required
def collection_report(request):
    """Report showing collections by period"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    # Default to current month
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today.replace(day=1))
    end_date = request.GET.get('end_date', today)
    
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get payments in period
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).select_related('invoice', 'invoice__student', 'received_by')
    
    # Group by payment method
    by_method = {}
    for method_code, method_name in Payment.PAYMENT_METHOD_CHOICES:
        amount = payments.filter(payment_method=method_code).aggregate(
            total=Sum('amount')
        )['total'] or 0
        by_method[method_name] = amount
    
    # Group by date
    daily_collections = {}
    for payment in payments:
        date_key = payment.payment_date
        if date_key not in daily_collections:
            daily_collections[date_key] = 0
        daily_collections[date_key] += payment.amount
    
    # Sort by date
    daily_collections = dict(sorted(daily_collections.items()))
    
    total_collected = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments,
        'total_collected': total_collected,
        'by_method': by_method,
        'daily_collections': daily_collections,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'finance/collection_report.html', context)


@login_required
def student_ledger(request, student_id):
    """Detailed financial ledger for a specific student"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    
    # Get all invoices
    invoices = Invoice.objects.filter(student=student).select_related(
        'fee_structure', 'fee_structure__term'
    ).order_by('-issue_date')
    
    # Build ledger entries
    ledger_entries = []
    running_balance = 0
    
    for invoice in invoices:
        # Invoice entry (debit)
        running_balance += invoice.total_amount
        ledger_entries.append({
            'date': invoice.issue_date,
            'type': 'invoice',
            'description': f"Invoice #{invoice.invoice_number} - {invoice.fee_structure.name}",
            'debit': invoice.total_amount,
            'credit': 0,
            'balance': running_balance,
            'reference': invoice
        })
        
        # Payment entries (credit)
        payments = Payment.objects.filter(invoice=invoice).order_by('payment_date')
        for payment in payments:
            running_balance -= payment.amount
            ledger_entries.append({
                'date': payment.payment_date,
                'type': 'payment',
                'description': f"Payment - {payment.get_payment_method_display()} ({payment.transaction_reference})",
                'debit': 0,
                'credit': payment.amount,
                'balance': running_balance,
                'reference': payment
            })
    
    # Sort by date
    ledger_entries.sort(key=lambda x: x['date'])
    
    # Recalculate running balance after sorting
    running_balance = 0
    for entry in ledger_entries:
        running_balance += entry['debit'] - entry['credit']
        entry['balance'] = running_balance
    
    context = {
        'student': student,
        'ledger_entries': ledger_entries,
        'final_balance': running_balance,
    }
    
    return render(request, 'finance/student_ledger.html', context)


@login_required
def search_student_invoice(request):
    """Search for students to view/record payments"""
    if request.user.user_type not in ['admin', 'accountant']:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    
    students = []
    query = request.GET.get('q', '')
    
    if query:
        students = Student.objects.filter(
            Q(student_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        ).select_related('user', 'current_class')[:20]
        
        # Add financial info to each student
        for student in students:
            invoices = Invoice.objects.filter(student=student)
            total_invoiced = sum(inv.total_amount for inv in invoices)
            total_paid = Payment.objects.filter(
                invoice__in=invoices
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            student.total_invoiced = total_invoiced
            student.total_paid = total_paid
            student.balance = total_invoiced - total_paid
    
    context = {
        'students': students,
        'query': query,
    }
    
    return render(request, 'finance/search_student.html', context)



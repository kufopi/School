# finance/urls.py
from django.urls import path
from . import views
from .views import InitiatePaymentView, verify_payment
from .views import (
    accountant_dashboard, record_payment, payment_history,
    outstanding_report, collection_report, student_ledger,
    search_student_invoice
)

urlpatterns = [
    # Fee Categories
    path('fee-categories/', views.FeeCategoryListView.as_view(), name='fee_category_list'),
    path('fee-categories/add/', views.FeeCategoryCreateView.as_view(), name='fee_category_create'),
    path('fee-categories/<int:pk>/edit/', views.FeeCategoryUpdateView.as_view(), name='fee_category_update'),
    
    # Fee Items
    path('fee-items/', views.FeeItemListView.as_view(), name='fee_item_list'),
    path('fee-items/add/', views.FeeItemCreateView.as_view(), name='fee_item_create'),
    path('fee-items/<int:pk>/edit/', views.FeeItemUpdateView.as_view(), name='fee_item_update'),
    
    # Fee Structures
    path('fee-structures/', views.FeeStructureListView.as_view(), name='fee_structure_list'),
    path('fee-structures/add/', views.FeeStructureCreateView.as_view(), name='fee_structure_create'),
    path('fee-structures/<int:pk>/', views.FeeStructureDetailView.as_view(), name='fee_structure_detail'),
    path('fee-structures/<int:pk>/edit/', views.FeeStructureUpdateView.as_view(), name='fee_structure_update'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    
    # Payments
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('payments/add/<int:invoice_id>/', views.PaymentCreateView.as_view(), name='payment_create_for_invoice'),
    
    # Reports
    path('reports/fee-structures/', views.fee_structure_report, name='fee_structure_report'),
    path('reports/fee-structures/<int:term_id>/', views.fee_structure_report, name='fee_structure_report_term'),
    path('invoices/generate/<int:term_id>/', views.generate_term_invoices, name='generate_term_invoices'),

    path('invoice/<int:invoice_id>/pay/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('payment/verify/<int:invoice_id>/', verify_payment, name='verify_payment'),

    path('student-finance/<int:student_id>/', views.student_finance_dashboard, name='student_finance_dashboard'),
    path('student-finance/', views.student_finance_dashboard, name='my_finance_dashboard'),



    path('accountant/', accountant_dashboard, name='accountant_dashboard'),
    path('accountant/record-payment/', record_payment, name='record_payment'),
    path('accountant/record-payment/<int:invoice_id>/', record_payment, name='record_payment_invoice'),
    path('accountant/payment-history/', payment_history, name='payment_history'),
    path('accountant/outstanding/', outstanding_report, name='outstanding_report'),
    path('accountant/collections/', collection_report, name='collection_report'),
    path('accountant/ledger/<int:student_id>/', student_ledger, name='student_ledger'),
    path('accountant/search/', search_student_invoice, name='search_student_invoice'),
]
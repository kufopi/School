from django.urls import path
from .views import (SubjectListView, SubjectCreateView, ResultEntryView, 
                    TermReportView, ReportCommentView,TermReportPDFView)

urlpatterns = [
    path('subjects/', SubjectListView.as_view(), name='subject_list'),
    path('subjects/add/', SubjectCreateView.as_view(), name='subject_create'),
    path('results/add/', ResultEntryView.as_view(), name='result_entry'),
    path('reports/<int:pk>/', TermReportView.as_view(), name='term_report'),
    path('reports/<int:report_id>/comment/', ReportCommentView.as_view(), name='report_comment'),
    path('reports/<int:pk>/pdf/', TermReportPDFView.as_view(), name='term_report_pdf'),
]
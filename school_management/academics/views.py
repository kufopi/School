from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from .models import Subject, Class, Result, TermReport , ReportComment, SubjectGrade
from .forms import SubjectForm, ResultForm, ReportCommentForm
from django.shortcuts import get_object_or_404

class SubjectListView(ListView):
    model = Subject
    template_name = 'academics/subject_list.html'

class SubjectCreateView(CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'academics/subject_form.html'
    success_url = reverse_lazy('subject_list')

class ResultEntryView(CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'academics/result_form.html'
    
    def get_success_url(self):
        return reverse_lazy('term_report', kwargs={'pk': self.object.student.pk})
    

class TermReportView(DetailView):
    model = TermReport
    template_name = 'academics/term_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_results'] = self.object.get_subject_results()
        return context

class ReportCommentView(CreateView):
    model = ReportComment
    form_class = ReportCommentForm
    template_name = 'academics/report_comment_form.html'
    
    def form_valid(self, form):
        form.instance.report = TermReport.objects.get(pk=self.kwargs['report_id'])
        form.instance.added_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('term_report', kwargs={'pk': self.object.report.pk})
    

# academics/views.py
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import generate_term_report_pdf

class TermReportPDFView(DetailView):
    model = TermReport
    template_name = 'academics/term_report_pdf.html'
    
    def get(self, request, *args, **kwargs):
        report = self.get_object()
        pdf_buffer = generate_term_report_pdf(report)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        filename = f"report_{report.student.student_id}_{report.term.name.replace(' ', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    

def download_report_pdf(request, report_id):
    report = get_object_or_404(TermReport, pk=report_id)
    pdf_buffer = generate_term_report_pdf(report)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"report_{report.student.student_id}_{report.term.name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Subject, Class, ClassSubject, ExamType, TermReport, 
    Result, ReportComment, PredefinedComment,SubjectGrade
)
from django.db import models


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'get_class_count', 'get_student_count']
    search_fields = ['name', 'code']
    list_filter = ['name']
    ordering = ['name']
    
    def get_class_count(self, obj):
        return obj.classsubject_set.count()
    get_class_count.short_description = 'Classes Teaching'
    
    def get_student_count(self, obj):
        return Result.objects.filter(subject=obj).values('student').distinct().count()
    get_student_count.short_description = 'Total Students'


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    # Updated list_display to include arm and better organization
    list_display = ['get_full_name', 'short_name', 'level', 'arm', 'get_student_count', 'get_subject_count']
    list_filter = ['level', 'arm']  # Added arm filter
    search_fields = ['name', 'short_name', 'arm']  # Added arm to search
    ordering = ['level', 'arm']  # Updated ordering to include arm
    list_editable = ['arm']  # Allow quick editing of arm
    
    fieldsets = (
        ('Class Information', {
            'fields': ('name', 'short_name', 'level', 'arm')  # Added arm field
        }),
    )
    
    def get_full_name(self, obj):
        """Display full class name with arm"""
        return obj.full_name
    get_full_name.short_description = 'Full Class Name'
    get_full_name.admin_order_field = 'name'
    
    def get_student_count(self, obj):
        return obj.student_set.count()
    get_student_count.short_description = 'Students'
    
    def get_subject_count(self, obj):
        return obj.classsubject_set.count()
    get_subject_count.short_description = 'Subjects'
    
    # Add custom actions for bulk operations
    actions = ['duplicate_class_structure']
    
    def duplicate_class_structure(self, request, queryset):
        """Duplicate class structure for creating multiple arms"""
        duplicated_count = 0
        for class_obj in queryset:
            if not class_obj.arm:
                # Create Alpha and Beta versions
                for arm in ['Alpha', 'Beta']:
                    new_class = Class.objects.create(
                        name=class_obj.name,
                        short_name=class_obj.short_name,
                        level=class_obj.level,
                        arm=arm
                    )
                    # Copy class subjects
                    for class_subject in class_obj.classsubject_set.all():
                        ClassSubject.objects.create(
                            class_info=new_class,
                            subject=class_subject.subject,
                            teacher=class_subject.teacher
                        )
                    duplicated_count += 1
        
        self.message_user(request, f'Successfully duplicated {duplicated_count} class structures.')
    duplicate_class_structure.short_description = 'Create multiple arms for selected classes'


class ClassSubjectInline(admin.TabularInline):
    model = ClassSubject
    extra = 1
    fields = ['subject', 'teacher']
    autocomplete_fields = ['subject']


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ['get_class_display', 'subject', 'teacher', 'get_student_count']
    list_filter = ['class_info__level', 'class_info__arm', 'subject', 'teacher']  # Updated filters
    search_fields = ['class_info__name', 'class_info__arm', 'subject__name', 'teacher__user__first_name', 'teacher__user__last_name']
    autocomplete_fields = ['class_info', 'subject']
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('class_info', 'subject', 'teacher')
        }),
    )
    
    def get_class_display(self, obj):
        """Show full class name with arm"""
        return obj.class_info.full_name
    get_class_display.short_description = 'Class'
    get_class_display.admin_order_field = 'class_info__level'
    
    def get_student_count(self, obj):
        return obj.class_info.student_set.count()
    get_student_count.short_description = 'Students in Class'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('class_info', 'subject', 'teacher__user')


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'max_score', 'is_final', 'get_weight_display', 'get_usage_count']
    list_editable = ['weight', 'max_score', 'is_final']  # Added editable fields
    list_filter = ['is_final']  # Added filter
    search_fields = ['name']
    ordering = ['weight']
    
    fieldsets = (
        ('Exam Type Information', {
            'fields': ('name', 'weight', 'max_score', 'is_final')  # Added missing fields
        }),
    )
    
    def get_weight_display(self, obj):
        return f"{obj.weight}%"
    get_weight_display.short_description = 'Weight'
    
    def get_usage_count(self, obj):
        return obj.result_set.count()
    get_usage_count.short_description = 'Results Count'


class ResultInline(admin.TabularInline):
    model = Result
    extra = 1
    fields = ['exam_type', 'score', 'recorded_by']
    readonly_fields = ['date_recorded']

class SubjectGradeInline(admin.TabularInline):
    model = SubjectGrade
    extra = 0
    readonly_fields = ['final_score', 'grade']
    can_delete = False
    show_change_link = True

class ReportCommentInline(admin.StackedInline):
    model = ReportComment
    extra = 0
    fields = ['comment_type', 'comment', 'added_by']
    readonly_fields = ['date_added']


# Replace the TermReportAdmin methods in your admin.py with these corrected versions:

@admin.register(TermReport)
class TermReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'created_by', 'get_results_count', 'get_comments_count', 'get_status', 'is_published', 'date_created']  # Added created_by
    list_filter = ['term', 'student__current_class__level', 'student__current_class__arm', 'is_published']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    readonly_fields = ['date_created', 'created_by']  # Added created_by as readonly
    autocomplete_fields = ['student', 'term', 'created_by']  # Added autocomplete
    
    # Add created_by to the form handling
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Use the correct reverse relationship name - 'result' (singular)
        qs = qs.annotate(results_count=Count('result', distinct=True))
        return qs
    
    def get_results_count(self, obj):
        return obj.results_count
    get_results_count.short_description = 'Results'
    get_results_count.admin_order_field = 'results_count'
    
    def get_comments_count(self, obj):
        return obj.reportcomment_set.count()
    get_comments_count.short_description = 'Comments'
    
    def publish_reports(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'Successfully published {updated} reports.')
    publish_reports.short_description = 'Publish selected reports'
    
    def unpublish_reports(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Successfully unpublished {updated} reports.')
    unpublish_reports.short_description = 'Unpublish selected reports'
    
    def get_status(self, obj):
        results_count = obj.results_count
        comments_count = obj.reportcomment_set.count()
        if results_count == 0:
            color = 'red'
            status = 'No Results'
        elif comments_count == 0:
            color = 'orange'
            status = 'Incomplete'
        else:
            color = 'green'
            status = 'Complete'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_status.short_description = 'Status'

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['get_student_display', 'get_student_class', 'subject', 'exam_type', 'get_score_display', 'get_grade', 'term', 'recorded_by', 'date_recorded']
    list_filter = ['exam_type', 'term', 'subject', 'date_recorded']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id', 'subject__name']
    autocomplete_fields = ['student', 'subject', 'term', 'exam_type', 'term_report', 'recorded_by']  # Added term_report
    
    fieldsets = (
        ('Result Information', {
            'fields': ('student', 'term', 'term_report', 'subject', 'exam_type', 'score')  # Added term_report
        }),
        ('Recording Information', {
            'fields': ('recorded_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_display(self, obj):
        return str(obj.student)
    get_student_display.short_description = 'Student'
    
    def get_student_class(self, obj):
        if hasattr(obj.student, 'current_class'):
            return obj.student.current_class.full_name
        return "No Class"
    get_student_class.short_description = 'Class'
    
    def get_score_display(self, obj):
        return f"{obj.score:.1f}/{obj.exam_type.max_score}"
    get_score_display.short_description = 'Score'
    
    def get_grade(self, obj):
        results = Result.objects.filter(student=obj.student, term=obj.term, subject=obj.subject)
        
        total_weighted_score = sum(
            (float(r.score) / float(r.exam_type.max_score)) * float(r.exam_type.weight)
            for r in results
        )
        
        total_weight = sum(r.exam_type.weight for r in results)
        
        if total_weight > 0:
            return TermReport.calculate_subject_grade(obj, total_weighted_score)
        return 'F'
    get_grade.short_description = 'Grade'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'term', 'subject', 'exam_type', 'recorded_by')


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ['get_student_display', 'get_student_class', 'comment_type', 'get_comment_preview', 'date_added', 'added_by']
    list_filter = ['comment_type', 'date_added', 'report__student__current_class__level', 'report__student__current_class__arm']
    search_fields = ['report__student__user__first_name', 'report__student__user__last_name', 'comment']
    readonly_fields = ['date_added', 'added_by']  # Added added_by as readonly
    autocomplete_fields = ['report', 'added_by']  # Added autocomplete
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('report', 'comment_type', 'comment')
        }),
        ('Tracking Information', {
            'fields': ('added_by', 'date_added'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set added_by on creation
            obj.added_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_student_display(self, obj):
        return str(obj.report.student)
    get_student_display.short_description = 'Student'
    
    def get_student_class(self, obj):
        """Show student's class with arm"""
        if hasattr(obj.report.student, 'current_class') and obj.report.student.current_class:
            return obj.report.student.current_class.full_name
        return "No Class"
    get_student_class.short_description = 'Class'
    
    def get_comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    get_comment_preview.short_description = 'Comment Preview'


@admin.register(PredefinedComment)
class PredefinedCommentAdmin(admin.ModelAdmin):
    list_display = ['comment_type', 'get_text_preview', 'get_usage_indicator']
    list_filter = ['comment_type']
    search_fields = ['text']
    
    fieldsets = (
        ('Predefined Comment', {
            'fields': ('comment_type', 'text')
        }),
    )
    
    def get_text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    get_text_preview.short_description = 'Comment Text'
    
    def get_usage_indicator(self, obj):
        return format_html(
            '<span style="color: green;">✓ Ready to Use</span>'
        )
    get_usage_indicator.short_description = 'Status'


# Enhanced Class Admin with Subject Inline
# Replace the EnhancedClassAdmin with this corrected version
class EnhancedClassAdmin(ClassAdmin):
    inlines = [ClassSubjectInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('classsubject_set__subject', 'classsubject_set__teacher')


@admin.register(SubjectGrade)
class SubjectGradeAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'subject', 'final_score', 'grade', 'position']
    list_filter = ['report__term', 'subject']
    readonly_fields = ['final_score', 'grade']
    
    def get_student(self, obj):
        return obj.report.student
    get_student.short_description = 'Student'


# Custom Admin Site Customizations
admin.site.site_header = "School Management System"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Administration"

# Register enhanced version if needed
admin.site.unregister(Class)
admin.site.register(Class, EnhancedClassAdmin)
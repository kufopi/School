from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Student, StudentMedicalHistory, StudentHealthRecord, BehaviorAssessment, AttendanceRecord


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'get_full_name', 'current_class', 'gender', 'admission_date', 'is_active', 'photo_preview']
    list_filter = ['gender', 'is_active', 'admission_date', 'current_class']
    search_fields = ['student_id', 'user__first_name', 'user__last_name', 'user__email']
    list_editable = ['is_active']
    readonly_fields = ['photo_preview']
    date_hierarchy = 'admission_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'student_id', 'date_of_birth', 'gender')
        }),
        ('Academic Information', {
            'fields': ('current_class', 'admission_date', 'is_active')
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 50%;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = 'Photo Preview'


class StudentMedicalHistoryInline(admin.TabularInline):
    model = StudentMedicalHistory
    extra = 1
    fields = ['condition', 'diagnosed_date', 'is_chronic', 'description', 'treatment']


@admin.register(StudentMedicalHistory)
class StudentMedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'condition', 'diagnosed_date', 'is_chronic']
    list_filter = ['is_chronic', 'diagnosed_date', 'condition']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id', 'condition']
    date_hierarchy = 'diagnosed_date'
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Medical Details', {
            'fields': ('condition', 'diagnosed_date', 'is_chronic', 'description', 'treatment')
        }),
    )


class StudentHealthRecordInline(admin.TabularInline):
    model = StudentHealthRecord
    extra = 1
    readonly_fields = ['bmi']
    fields = ['record_date', 'height', 'weight', 'bmi', 'notes']


@admin.register(StudentHealthRecord)
class StudentHealthRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'record_date', 'height', 'weight', 'bmi', 'get_bmi_status']
    list_filter = ['record_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    readonly_fields = ['bmi']
    date_hierarchy = 'record_date'
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Health Measurements', {
            'fields': ('record_date', 'height', 'weight', 'bmi', 'notes')
        }),
    )
    
    def get_bmi_status(self, obj):
        if obj.bmi is not None:
            bmi_value = float(obj.bmi)
            if bmi_value < 18.5:
                color = 'blue'
                status = 'Underweight'
            elif bmi_value < 25:
                color = 'green'
                status = 'Normal'
            elif bmi_value < 30:
                color = 'orange'
                status = 'Overweight'
            else:
                color = 'red'
                status = 'Obese'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status
            )
        return "N/A"
    get_bmi_status.short_description = 'BMI Status'


@admin.register(BehaviorAssessment)
class BehaviorAssessmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'assessment_date', 'assessed_by', 'get_overall_score', 'get_performance_indicator']
    list_filter = ['term', 'assessment_date', 'assessed_by']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    date_hierarchy = 'assessment_date'
    
    fieldsets = (
        ('Assessment Information', {
            'fields': ('student', 'term', 'assessed_by')
        }),
        ('Behavior Skills Assessment', {
            'fields': ('participation', 'responsibility', 'creativity', 'cooperation'),
            'description': 'Rate each skill from 1 (Needs Improvement) to 5 (Excellent)'
        }),
    )
    
    def get_overall_score(self, obj):
        total = obj.participation + obj.responsibility + obj.creativity + obj.cooperation
        average = total / 4
        return f"{average:.1f}/5.0"
    get_overall_score.short_description = 'Overall Score'
    
    def get_performance_indicator(self, obj):
        total = obj.participation + obj.responsibility + obj.creativity + obj.cooperation
        average = total / 4
        
        if average >= 4.5:
            color = 'green'
            status = 'Excellent'
        elif average >= 3.5:
            color = 'blue'
            status = 'Good'
        elif average >= 2.5:
            color = 'orange'
            status = 'Satisfactory'
        elif average >= 1.5:
            color = 'red'
            status = 'Developing'
        else:
            color = 'darkred'
            status = 'Needs Improvement'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_performance_indicator.short_description = 'Performance'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'days_present', 'days_absent', 'get_total_days', 'get_attendance_rate', 'get_attendance_status']
    list_filter = ['term']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__student_id']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'term')
        }),
        ('Attendance Data', {
            'fields': ('days_present', 'days_absent')
        }),
    )
    
    def get_total_days(self, obj):
        return obj.days_present + obj.days_absent
    get_total_days.short_description = 'Total Days'
    
    def get_attendance_rate(self, obj):
        return f"{obj.attendance_rate:.1f}%"
    get_attendance_rate.short_description = 'Attendance Rate'
    
    def get_attendance_status(self, obj):
        rate = obj.attendance_rate
        
        if rate >= 95:
            color = 'green'
            status = 'Excellent'
        elif rate >= 85:
            color = 'blue'
            status = 'Good'
        elif rate >= 75:
            color = 'orange'
            status = 'Fair'
        else:
            color = 'red'
            status = 'Poor'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_attendance_status.short_description = 'Status'


# Enhanced Student Admin with Inlines
class EnhancedStudentAdmin(StudentAdmin):
    inlines = [StudentMedicalHistoryInline, StudentHealthRecordInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'current_class')


# Uncomment the line below if you want to use the enhanced version with inlines
admin.site.unregister(Student)
admin.site.register(Student, EnhancedStudentAdmin)
from django.contrib import admin
from .models import Teacher, ClassTeacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'staff_id', 'qualification', 'specialization', 'date_employed', 'is_active')
    list_filter = ('is_active', 'date_employed', 'qualification', 'specialization')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name', 'user__email', 'qualification', 'specialization')
    list_editable = ('is_active',)
    readonly_fields = ('date_employed',)
    ordering = ('user__first_name', 'user__last_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'staff_id')
        }),
        ('Professional Details', {
            'fields': ('qualification', 'specialization', 'date_employed')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ('get_teacher_name', 'get_staff_id', 'class_assigned', 'academic_session')
    list_filter = ('academic_session', 'class_assigned')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'teacher__staff_id', 'class_assigned__name')
    ordering = ('academic_session', 'class_assigned')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('teacher', 'class_assigned', 'academic_session')
        }),
    )
    
    def get_teacher_name(self, obj):
        return obj.teacher.user.get_full_name()
    get_teacher_name.short_description = 'Teacher Name'
    get_teacher_name.admin_order_field = 'teacher__user__first_name'
    
    def get_staff_id(self, obj):
        return obj.teacher.staff_id
    get_staff_id.short_description = 'Staff ID'
    get_staff_id.admin_order_field = 'teacher__staff_id'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__user', 'class_assigned', 'academic_session')
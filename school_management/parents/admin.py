from django.contrib import admin
from .models import Parent, ParentStudent

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'relationship', 'phone', 'occupation', 'get_email')
    list_filter = ('relationship', 'occupation')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone', 'occupation')
    ordering = ('user__first_name', 'user__last_name')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'relationship')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address')
        }),
        ('Professional Information', {
            'fields': ('occupation',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

class ParentStudentInline(admin.TabularInline):
    model = ParentStudent
    extra = 1
    fields = ('student', 'is_primary')
    verbose_name = "Child"
    verbose_name_plural = "Children"

@admin.register(ParentStudent)
class ParentStudentAdmin(admin.ModelAdmin):
    list_display = ('get_parent_name', 'get_student_name', 'is_primary', 'get_parent_relationship')
    list_filter = ('is_primary', 'parent__relationship')
    search_fields = ('parent__user__first_name', 'parent__user__last_name', 'student__user__first_name', 'student__user__last_name')
    ordering = ('parent__user__first_name', 'student__user__first_name')
    
    fieldsets = (
        ('Relationship Details', {
            'fields': ('parent', 'student', 'is_primary')
        }),
    )
    
    def get_parent_name(self, obj):
        return obj.parent.user.get_full_name()
    get_parent_name.short_description = 'Parent Name'
    get_parent_name.admin_order_field = 'parent__user__first_name'
    
    def get_student_name(self, obj):
        return obj.student.user.get_full_name()
    get_student_name.short_description = 'Student Name'
    get_student_name.admin_order_field = 'student__user__first_name'
    
    def get_parent_relationship(self, obj):
        return obj.parent.get_relationship_display()
    get_parent_relationship.short_description = 'Relationship'
    get_parent_relationship.admin_order_field = 'parent__relationship'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent__user', 'student__user')

# Add the inline to ParentAdmin
ParentAdmin.inlines = [ParentStudentInline]
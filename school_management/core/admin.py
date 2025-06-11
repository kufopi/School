# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SchoolSession, SchoolTerm

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_approved', 'is_staff')
    list_filter = ('user_type', 'is_approved', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_approved', 'user_type', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'phone', 'user_type'),
        }),
    )
    
    actions = ['approve_users']
    
    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
    approve_users.short_description = "Approve selected users"

# School Session Admin
class SchoolSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_editable = ('is_current',)
    list_filter = ('is_current',)
    search_fields = ('name',)
    date_hierarchy = 'start_date'
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            # Ensure only one session is current
            SchoolSession.objects.filter(is_current=True).exclude(id=obj.id).update(is_current=False)
        super().save_model(request, obj, form, change)

# School Term Admin
class SchoolTermAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'start_date', 'end_date', 'is_current')
    list_editable = ('is_current',)
    list_filter = ('is_current', 'session')
    search_fields = ('name', 'session__name')
    date_hierarchy = 'start_date'
    autocomplete_fields = ['session']
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            # Ensure only one term is current
            SchoolTerm.objects.filter(is_current=True).exclude(id=obj.id).update(is_current=False)
        super().save_model(request, obj, form, change)

# Register your models here
admin.site.register(User, CustomUserAdmin)
admin.site.register(SchoolSession, SchoolSessionAdmin)
admin.site.register(SchoolTerm, SchoolTermAdmin)

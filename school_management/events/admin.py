from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_date_range', 'location', 'organizer', 'get_status', 'get_duration', 'is_published']
    list_filter = ['is_published', 'start_date', 'organizer']
    search_fields = ['title', 'description', 'location', 'organizer__user__first_name', 'organizer__user__last_name']
    list_editable = ['is_published']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'location', 'organizer')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
    )
    
    def get_date_range(self, obj):
        start = obj.start_date.strftime('%Y-%m-%d %H:%M')
        end = obj.end_date.strftime('%Y-%m-%d %H:%M')
        
        # If same day, show date once
        if obj.start_date.date() == obj.end_date.date():
            date_part = obj.start_date.strftime('%Y-%m-%d')
            start_time = obj.start_date.strftime('%H:%M')
            end_time = obj.end_date.strftime('%H:%M')
            return f"{date_part} ({start_time} - {end_time})"
        else:
            return f"{start} to {end}"
    get_date_range.short_description = 'Date & Time'
    
    def get_status(self, obj):
        now = timezone.now()
        
        if obj.end_date < now:
            color = 'gray'
            status = 'Completed'
        elif obj.start_date <= now <= obj.end_date:
            color = 'green'
            status = 'Ongoing'
        elif obj.start_date > now:
            color = 'blue'
            status = 'Upcoming'
        else:
            color = 'orange'
            status = 'Scheduled'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_status.short_description = 'Status'
    
    def get_duration(self, obj):
        duration = obj.end_date - obj.start_date
        
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            if hours > 0:
                return f"{days}d {hours}h {minutes}m"
            else:
                return f"{days}d {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    get_duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organizer__user')


# Custom Admin Actions
@admin.action(description='Mark events as published')
def mark_as_published(modeladmin, request, queryset):
    queryset.update(is_published=True)

@admin.action(description='Mark events as unpublished')
def mark_as_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)

# Add actions to EventAdmin
EventAdmin.actions = [mark_as_published, mark_as_unpublished]


# Custom admin site configuration
admin.site.site_header = "School Management System"
admin.site.site_title = "School Admin"
admin.site.index_title = "Welcome to School Administration"
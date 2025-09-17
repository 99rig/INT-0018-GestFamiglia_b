from django.contrib import admin
from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ['version_name', 'version_code', 'is_mandatory', 'created_at']
    list_filter = ['is_mandatory', 'created_at']
    search_fields = ['version_name', 'release_notes']
    ordering = ['-version_code']
    
    fieldsets = [
        ('Informazioni Versione', {
            'fields': ['version_name', 'version_code', 'release_notes']
        }),
        ('File e Distribuzione', {
            'fields': ['apk_file', 'is_mandatory', 'min_supported_version']
        }),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['version_code']
        return []
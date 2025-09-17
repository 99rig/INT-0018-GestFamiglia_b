from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline per gestire il profilo direttamente dall'utente"""
    model = UserProfile
    can_delete = False
    extra = 0
    fields = ['role', 'family_role', 'phone_number', 'birth_date', 'profile_picture', 'bio']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizzato per User"""
    inlines = [UserProfileInline]
    
    list_display = [
        'email', 'username', 'first_name', 'last_name', 
        'profile_role', 'profile_family_role', 'is_active', 'is_staff'
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'profile__role', 'profile__family_role']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informazioni Personali', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permessi', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Date Importanti', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
        ('Informazioni Personali', {
            'fields': ('first_name', 'last_name'),
        }),
    )
    
    def profile_role(self, obj):
        if hasattr(obj, 'profile'):
            colors = {'master': 'green', 'familiare': 'blue'}
            color = colors.get(obj.profile.role, 'black')
            return format_html(
                '<span style="color: {};">● {}</span>',
                color, obj.profile.get_role_display()
            )
        return "-"
    profile_role.short_description = "Ruolo Sistema"
    
    def profile_family_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_family_role_display()
        return "-"
    profile_family_role.short_description = "Ruolo Famiglia"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin per UserProfile"""
    list_display = [
        'user_display', 'role', 'family_role', 'phone_number', 
        'birth_date', 'created_at'
    ]
    list_filter = ['role', 'family_role', 'created_at']
    search_fields = ['user__email', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utente', {
            'fields': ('user',)
        }),
        ('Ruoli', {
            'fields': ('role', 'family_role')
        }),
        ('Informazioni Personali', {
            'fields': ('phone_number', 'birth_date', 'profile_picture', 'bio')
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        return f"{obj.user.get_full_name() or obj.user.email}"
    user_display.short_description = "Utente"

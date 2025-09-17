from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Subcategory


class SubcategoryInline(admin.TabularInline):
    """Inline per gestire le sottocategorie direttamente dalla categoria"""
    model = Subcategory
    extra = 1
    fields = ['name', 'description', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'type_display', 'monthly_budget', 'subcategory_count',
        'is_active', 'created_at'
    ]
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'subcategory_count']
    
    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('name', 'description', 'type', 'is_active')
        }),
        ('Aspetto Visivo', {
            'fields': ('icon', 'color'),
            'classes': ('collapse',)
        }),
        ('Budget', {
            'fields': ('monthly_budget',)
        }),
        ('Statistiche', {
            'fields': ('subcategory_count',),
            'classes': ('collapse',)
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [SubcategoryInline]
    
    def type_display(self, obj):
        colors = {
            'necessaria': 'green',
            'extra': 'blue'
        }
        color = colors.get(obj.type, 'black')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_type_display()
        )
    type_display.short_description = "Tipo"
    
    def subcategory_count(self, obj):
        count = obj.subcategories.count()
        active_count = obj.subcategories.filter(is_active=True).count()
        return f"{active_count} attive / {count} totali"
    subcategory_count.short_description = "Sottocategorie"


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category_display', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('category', 'name', 'description', 'is_active')
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def category_display(self, obj):
        type_colors = {
            'necessaria': 'green',
            'extra': 'blue'
        }
        color = type_colors.get(obj.category.type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.category.name
        )
    category_display.short_description = "Categoria"

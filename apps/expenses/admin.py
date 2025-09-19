from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Expense, RecurringExpense, ExpenseAttachment, ExpenseQuota


class ExpenseQuotaInline(admin.TabularInline):
    """Inline per gestire le quote direttamente dalla spesa"""
    model = ExpenseQuota
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'is_overdue_display']
    fields = [
        'quota_number', 'amount', 'due_date', 'is_paid', 'paid_date',
        'payment_method', 'notes', 'is_overdue_display'
    ]
    
    def is_overdue_display(self, obj):
        if obj.pk and obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Scaduta</span>')
        elif obj.pk and not obj.is_paid:
            days = obj.days_until_due()
            if days is not None:
                if days < 0:
                    return format_html('<span style="color: red;">⚠️ Scaduta da {} giorni</span>', abs(days))
                elif days <= 7:
                    return format_html('<span style="color: orange;">⏰ Scade tra {} giorni</span>', days)
                else:
                    return format_html('<span style="color: green;">✓ Scade tra {} giorni</span>', days)
        return "✓ Pagata" if obj.pk and obj.is_paid else "-"
    is_overdue_display.short_description = "Stato scadenza"


class ExpenseAttachmentInline(admin.TabularInline):
    """Inline per gestire gli allegati"""
    model = ExpenseAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'description', 'user', 'amount', 'date', 'category', 'status_display',
        'payment_progress', 'shared_count', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'payment_method', 'date', 'is_recurring',
        'created_at'
    ]
    search_fields = ['description', 'notes', 'user__username', 'category__name']
    date_hierarchy = 'date'
    readonly_fields = [
        'created_at', 'updated_at', 'payment_progress', 'total_paid_amount',
        'remaining_amount', 'has_quote_display'
    ]
    
    class Media:
        js = ('admin/js/dynamic_subcategory.js',)
    
    fieldsets = (
        ('Informazioni Generali', {
            'fields': (
                'user', 'description', 'amount', 'date', 'status',
                'payment_method', 'notes'
            )
        }),
        ('Categorizzazione', {
            'fields': ('category', 'subcategory')
        }),
        ('Budget e Pianificazione', {
            'fields': ('budget',),
            'classes': ('collapse',)
        }),
        ('Condivisione', {
            'fields': ('shared_with',),
            'classes': ('collapse',)
        }),
        ('File e Documenti', {
            'fields': ('receipt',),
            'classes': ('collapse',)
        }),
        ('Stato Quote', {
            'fields': (
                'has_quote_display', 'payment_progress', 'total_paid_amount',
                'remaining_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Opzioni Avanzate', {
            'fields': ('is_recurring',),
            'classes': ('collapse',)
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ExpenseQuotaInline, ExpenseAttachmentInline]
    filter_horizontal = ['shared_with']
    
    def status_display(self, obj):
        colors = {
            'pagata': 'green',
            'da_pagare': 'red',
            'parzialmente_pagata': 'orange',
            'ricorrente': 'blue',
            'annullata': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Stato"
    
    def payment_progress(self, obj):
        if not obj.has_quote():
            return "N/A"
        
        percentage = obj.get_payment_progress_percentage()
        paid_count = obj.get_paid_quote_count()
        total_count = obj.get_total_quote_count()
        
        if percentage == 100:
            color = 'green'
        elif percentage > 0:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}% ({}/{})</span>',
            color, float(percentage), paid_count, total_count
        )
    payment_progress.short_description = "Progresso Quote"
    
    def shared_count(self, obj):
        count = obj.shared_with.count()
        if count > 0:
            return "👥 {}".format(count)
        return "-"
    shared_count.short_description = "Condivisa"
    
    def has_quote_display(self, obj):
        return "✓ Sì" if obj.has_quote() else "✗ No"
    has_quote_display.short_description = "Ha Quote"
    
    def total_paid_amount(self, obj):
        return "€{}".format(obj.get_total_paid_amount())
    total_paid_amount.short_description = "Importo Pagato"
    
    def remaining_amount(self, obj):
        return "€{}".format(obj.get_remaining_amount())
    remaining_amount.short_description = "Importo Rimanente"


@admin.register(ExpenseQuota)
class ExpenseQuotaAdmin(admin.ModelAdmin):
    list_display = [
        'expense_link', 'quota_number', 'amount', 'due_date',
        'is_paid_display', 'paid_date', 'status_display', 'payment_method'
    ]
    list_filter = [
        'is_paid', 'payment_method', 'due_date', 'created_at',
        'expense__status', 'expense__category'
    ]
    search_fields = [
        'expense__description', 'expense__user__username', 'notes'
    ]
    date_hierarchy = 'due_date'
    readonly_fields = ['created_at', 'updated_at', 'is_overdue_display', 'days_until_due_display']
    
    fieldsets = (
        ('Informazioni Quota', {
            'fields': (
                'expense', 'quota_number', 'amount', 'due_date'
            )
        }),
        ('Stato Pagamento', {
            'fields': (
                'is_paid', 'paid_date', 'payment_method'
            )
        }),
        ('Note e Dettagli', {
            'fields': ('notes',)
        }),
        ('Stato Scadenza', {
            'fields': ('is_overdue_display', 'days_until_due_display'),
            'classes': ('collapse',)
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def expense_link(self, obj):
        url = reverse('admin:expenses_expense_change', args=[obj.expense.pk])
        return format_html('<a href="{}">{}</a>', url, obj.expense.description)
    expense_link.short_description = "Spesa"
    
    def is_paid_display(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✓ Pagata</span>')
        else:
            return format_html('<span style="color: red;">○ Da Pagare</span>')
    is_paid_display.short_description = "Pagata"
    
    def status_display(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✓ Completata</span>')
        elif obj.is_overdue:
            return format_html('<span style="color: red;">⚠️ Scaduta</span>')
        else:
            days = obj.days_until_due()
            if days is not None:
                if days <= 7:
                    return format_html('<span style="color: orange;">⏰ Scade presto</span>')
                else:
                    return format_html('<span style="color: green;">⏰ In scadenza</span>')
        return "⏳ In attesa"
    status_display.short_description = "Stato"
    
    def is_overdue_display(self, obj):
        return "✓ Sì" if obj.is_overdue else "✗ No"
    is_overdue_display.short_description = "Scaduta"
    
    def days_until_due_display(self, obj):
        days = obj.days_until_due()
        if days is None:
            return "N/A (Pagata)"
        elif days < 0:
            return "Scaduta da {} giorni".format(abs(days))
        elif days == 0:
            return "Scade oggi"
        else:
            return "Scade tra {} giorni".format(days)
    days_until_due_display.short_description = "Giorni alla Scadenza"


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'description', 'user', 'amount', 'frequency', 'start_date',
        'end_date', 'is_active', 'last_generated'
    ]
    list_filter = [
        'frequency', 'is_active', 'category', 'start_date', 'end_date'
    ]
    search_fields = ['description', 'user__username', 'category__name']
    readonly_fields = ['last_generated', 'created_at', 'updated_at']
    filter_horizontal = ['shared_with']
    
    class Media:
        js = ('admin/js/dynamic_subcategory.js',)


@admin.register(ExpenseAttachment)
class ExpenseAttachmentAdmin(admin.ModelAdmin):
    list_display = ['expense', 'description', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['expense__description', 'description']
    readonly_fields = ['uploaded_at']



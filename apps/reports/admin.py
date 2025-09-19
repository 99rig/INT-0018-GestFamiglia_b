from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db import models
from .models import SpendingPlan, PlannedExpense


class PlannedExpenseInline(admin.TabularInline):
    """Inline per gestire le spese pianificate direttamente dal piano"""
    model = PlannedExpense
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'completion_display']
    fields = [
        'description', 'amount', 'category', 'subcategory', 'priority',
        'due_date', 'is_completed', 'completion_display', 'is_recurring', 'installment_number'
    ]

    def completion_display(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">✓ Completata</span>')
        else:
            return format_html('<span style="color: orange;">○ Da completare</span>')
    completion_display.short_description = "Stato"


@admin.register(SpendingPlan)
class SpendingPlanAdmin(admin.ModelAdmin):
    """Admin per i piani di spesa"""
    list_display = [
        'name', 'plan_type_display', 'period_display', 'total_budget',
        'expenses_count', 'total_planned', 'completion_percentage',
        'created_by', 'is_active', 'is_hidden'
    ]
    list_filter = [
        'plan_type', 'is_active', 'is_hidden', 'auto_generated',
        'start_date', 'created_at'
    ]
    search_fields = ['name', 'description', 'created_by__email']
    readonly_fields = [
        'created_at', 'updated_at', 'expenses_summary'
    ]
    filter_horizontal = ['users']

    fieldsets = (
        ('Informazioni Generali', {
            'fields': ('name', 'description', 'plan_type', 'total_budget', 'is_active')
        }),
        ('Periodo', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configurazioni Avanzate', {
            'fields': ('is_shared', 'is_hidden', 'auto_generated'),
            'classes': ('collapse',)
        }),
        ('Utenti', {
            'fields': ('users',),
            'classes': ('collapse',)
        }),
        ('Statistiche', {
            'fields': ('expenses_summary',),
            'classes': ('collapse',)
        }),
        ('Metadati', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [PlannedExpenseInline]

    def plan_type_display(self, obj):
        colors = {'monthly': 'blue', 'event': 'green', 'custom': 'orange'}
        color = colors.get(obj.plan_type, 'black')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.get_plan_type_display()
        )
    plan_type_display.short_description = "Tipo"

    def period_display(self, obj):
        if obj.start_date and obj.end_date:
            return "{} - {}".format(obj.start_date, obj.end_date)
        elif obj.start_date:
            return "Dal {}".format(obj.start_date)
        return "-"
    period_display.short_description = "Periodo"

    def expenses_count(self, obj):
        count = obj.planned_expenses.count()
        if count > 0:
            return "📋 {}".format(count)
        return "-"
    expenses_count.short_description = "Spese"

    def total_planned(self, obj):
        total = obj.planned_expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        return "€{}".format(total)
    total_planned.short_description = "Tot. Pianificato"

    def completion_percentage(self, obj):
        total = obj.planned_expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        if obj.total_budget and total > 0:
            percentage = (total / obj.total_budget) * 100
            if percentage >= 100:
                color = 'red'
            elif percentage >= 80:
                color = 'orange'
            else:
                color = 'green'

            return format_html(
                '<span style="color: {};">{}</span>',
                color, "{:.1f}%".format(float(percentage))
            )
        return "-"
    completion_percentage.short_description = "% Budget"

    def expenses_summary(self, obj):
        expenses = obj.planned_expenses.all()
        total_planned = expenses.aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        completed_count = expenses.filter(is_completed=True).count()
        pending_count = expenses.filter(is_completed=False).count()

        status_parts = []
        if completed_count > 0:
            status_parts.append("Completate: {}".format(completed_count))
        if pending_count > 0:
            status_parts.append("Da completare: {}".format(pending_count))

        status_text = '<br>'.join(status_parts) if status_parts else 'Nessuna spesa'
        budget_remaining = obj.total_budget - total_planned if obj.total_budget else 0

        return format_html(
            '<strong>Totale Pianificato:</strong> €{}<br>'
            '<strong>Budget Rimanente:</strong> €{}<br>'
            '<strong>Spese per Stato:</strong><br>{}',
            total_planned,
            budget_remaining,
            status_text
        )
    expenses_summary.short_description = "Riepilogo Spese"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlannedExpense)
class PlannedExpenseAdmin(admin.ModelAdmin):
    """Admin per le spese pianificate"""
    list_display = [
        'description', 'spending_plan_link', 'amount', 'category',
        'priority_display', 'due_date', 'completion_display', 'recurring_info'
    ]
    list_filter = [
        'is_completed', 'priority', 'category', 'is_recurring', 'due_date',
        'created_at', 'spending_plan__plan_type'
    ]
    search_fields = [
        'description', 'notes', 'spending_plan__name', 'category__name'
    ]
    date_hierarchy = 'due_date'
    readonly_fields = [
        'created_at', 'updated_at', 'parent_recurring_id'
    ]

    fieldsets = (
        ('Informazioni Generali', {
            'fields': (
                'spending_plan', 'description', 'amount', 'due_date', 'is_completed'
            )
        }),
        ('Categorizzazione', {
            'fields': ('category', 'subcategory', 'priority')
        }),
        ('Ricorrenza', {
            'fields': (
                'is_recurring', 'total_installments', 'installment_number',
                'recurring_frequency', 'parent_recurring_id'
            ),
            'classes': ('collapse',)
        }),
        ('Note e Dettagli', {
            'fields': ('notes',)
        }),
        ('Metadati', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def spending_plan_link(self, obj):
        url = reverse('admin:reports_spendingplan_change', args=[obj.spending_plan.pk])
        return format_html('<a href="{}">{}</a>', url, obj.spending_plan.name)
    spending_plan_link.short_description = "Piano"

    def completion_display(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">✓ Completata</span>')
        else:
            return format_html('<span style="color: orange;">○ Da completare</span>')
    completion_display.short_description = "Stato"

    def priority_display(self, obj):
        colors = {
            'urgent': 'red',
            'high': 'red',
            'medium': 'orange',
            'low': 'green'
        }
        color = colors.get(obj.priority, 'black')
        icons = {
            'urgent': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        icon = icons.get(obj.priority, '⚪')

        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_priority_display()
        )
    priority_display.short_description = "Priorità"

    def recurring_info(self, obj):
        if obj.is_recurring:
            if obj.total_installments and obj.installment_number:
                return format_html(
                    '<span style="color: orange;">🔄 {}/{}</span>',
                    obj.installment_number, obj.total_installments
                )
            return format_html('<span style="color: orange;">🔄 Ricorrente</span>')
        return "-"
    recurring_info.short_description = "Ricorrenza"

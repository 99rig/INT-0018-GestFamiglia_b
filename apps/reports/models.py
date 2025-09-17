from django.db import models
from django.conf import settings
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from apps.categories.models import Category
from apps.expenses.models import Expense
from decimal import Decimal


class SpendingPlan(models.Model):
    """
    Piano di spese per periodi personalizzabili - contenitore di spese pianificate
    """
    PLAN_TYPES = [
        ('monthly', 'Mensile'),
        ('seasonal', 'Stagionale'),
        ('event', 'Evento/Occasione'),
        ('yearly', 'Annuale'),
        ('custom', 'Personalizzato'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name="Nome piano spese"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrizione"
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        default='custom',
        verbose_name="Tipo piano"
    )
    start_date = models.DateField(
        verbose_name="Data inizio",
        default='2025-09-01'
    )
    end_date = models.DateField(
        verbose_name="Data fine",
        default='2025-09-30'
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='spending_plans',
        verbose_name="Utenti"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Attivo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Piano Spese"
        verbose_name_plural = "Piani Spese"
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    def get_total_planned_amount(self):
        """Calcola l'importo totale pianificato"""
        return self.planned_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_completed_expenses_amount(self):
        """Calcola l'importo delle spese completate"""
        return self.planned_expenses.filter(
            is_completed=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_pending_expenses_amount(self):
        """Calcola l'importo delle spese ancora da completare"""
        return self.planned_expenses.filter(
            is_completed=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_completion_percentage(self):
        """Calcola la percentuale di completamento"""
        total_planned = self.get_total_planned_amount()
        if total_planned > 0:
            completed = self.get_completed_expenses_amount()
            return (completed / total_planned * 100)
        return Decimal('0.00')

    def is_current(self):
        """Verifica se il piano è attivo nel periodo corrente"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class PlannedExpense(models.Model):
    """
    Spesa pianificata all'interno di un piano di spese
    """
    PRIORITY_CHOICES = [
        ('low', 'Bassa'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    spending_plan = models.ForeignKey(
        SpendingPlan,
        on_delete=models.CASCADE,
        related_name='planned_expenses',
        verbose_name="Piano spese"
    )
    description = models.CharField(
        max_length=200,
        verbose_name="Descrizione spesa"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo stimato",
        help_text="Importo stimato per questa spesa"
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )
    subcategory = models.ForeignKey(
        'categories.Subcategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sottocategoria"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorità"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data scadenza"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Note"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Completata"
    )
    actual_expense = models.ForeignKey(
        'expenses.Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Spesa reale",
        help_text="Spesa effettiva collegata a questa pianificazione"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Spesa Pianificata"
        verbose_name_plural = "Spese Pianificate"
        ordering = ['due_date', '-priority', 'created_at']

    def __str__(self):
        return f"{self.spending_plan.name} - {self.description}"

    def get_related_expenses(self):
        """Restituisce tutte le spese reali collegate a questa spesa pianificata"""
        from apps.expenses.models import Expense
        return Expense.objects.filter(planned_expense=self)

    def get_total_paid(self):
        """Calcola l'importo totale già pagato"""
        total = self.get_related_expenses().aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        return total

    def get_remaining_amount(self):
        """Calcola l'importo rimanente da pagare"""
        return self.amount - self.get_total_paid()

    def get_completion_percentage(self):
        """Calcola la percentuale di completamento"""
        if self.amount > 0:
            return float((self.get_total_paid() / self.amount) * 100)
        return 0.0

    def is_fully_paid(self):
        """Verifica se la spesa è completamente pagata"""
        return self.get_remaining_amount() <= Decimal('0.00')

    def is_partially_paid(self):
        """Verifica se la spesa è parzialmente pagata"""
        paid = self.get_total_paid()
        return paid > Decimal('0.00') and paid < self.amount

    def get_payment_status(self):
        """Restituisce lo stato del pagamento"""
        if self.is_fully_paid():
            return 'completed'
        elif self.is_partially_paid():
            return 'partial'
        elif self.due_date and self.due_date < timezone.now().date():
            return 'overdue'
        else:
            return 'pending'

    def mark_as_completed(self, actual_expense=None):
        """Segna la spesa come completata"""
        self.is_completed = True
        if actual_expense:
            self.actual_expense = actual_expense
        self.save()

    def get_status_display_class(self):
        """Ritorna la classe CSS per lo stato"""
        status = self.get_payment_status()
        if status == 'completed':
            return 'completed'
        elif status == 'partial':
            return 'partial'
        elif status == 'overdue':
            return 'overdue'
        elif self.priority == 'urgent':
            return 'urgent'
        elif self.priority == 'high':
            return 'high-priority'
        return 'pending'


# Alias per compatibilità (da deprecare)
Budget = SpendingPlan


class BudgetCategory(models.Model):
    """
    Modello per assegnare budget a specifiche categorie
    """
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='category_budgets',
        verbose_name="Budget"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Categoria"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget Categoria"
        verbose_name_plural = "Budget Categorie"
        unique_together = ['budget', 'category']
    
    def __str__(self):
        return f"{self.budget.name} - {self.category.name}: €{self.amount}"
    
    def get_spent_amount(self):
        """Calcola l'importo speso per questa categoria nel periodo del budget"""
        return Expense.objects.filter(
            user__in=self.budget.users.all(),
            category=self.category,
            date__gte=self.budget.start_date,
            date__lte=self.budget.end_date,
            status='pagata'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_percentage_used(self):
        """Calcola la percentuale utilizzata per questa categoria"""
        spent = self.get_spent_amount()
        if self.amount > 0:
            return (spent / self.amount * 100)
        return Decimal('0.00')


class SavingGoal(models.Model):
    """
    Modello per gli obiettivi di risparmio
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nome obiettivo"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrizione"
    )
    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo obiettivo"
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Importo attuale"
    )
    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data obiettivo"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='saving_goals',
        verbose_name="Utenti"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Completato"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Obiettivo di Risparmio"
        verbose_name_plural = "Obiettivi di Risparmio"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - €{self.target_amount}"
    
    def get_progress_percentage(self):
        """Calcola la percentuale di completamento"""
        if self.target_amount > 0:
            return (self.current_amount / self.target_amount * 100)
        return Decimal('0.00')
    
    def get_remaining_amount(self):
        """Calcola l'importo rimanente per raggiungere l'obiettivo"""
        return max(self.target_amount - self.current_amount, Decimal('0.00'))

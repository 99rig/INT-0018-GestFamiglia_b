from django.db import models
from django.conf import settings
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from apps.categories.models import Category
from apps.expenses.models import Expense
from decimal import Decimal


class UserSpendingPlanPreference(models.Model):
    """
    Preferenze personalizzate dell'utente per i piani di spesa
    Permette a ogni utente di avere pin e ordinamenti personalizzati
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='spending_plan_preferences',
        verbose_name="Utente"
    )
    spending_plan = models.ForeignKey(
        'SpendingPlan',
        on_delete=models.CASCADE,
        related_name='user_preferences',
        verbose_name="Piano di spesa"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Pinnato",
        help_text="Se True, il piano appare in cima alla lista per questo utente"
    )
    custom_order = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Ordinamento personalizzato",
        help_text="Permette all'utente di riordinare manualmente i piani"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Preferenza Piano Spese"
        verbose_name_plural = "Preferenze Piani Spese"
        unique_together = [('user', 'spending_plan')]
        indexes = [
            # Indice per lookup veloce delle preferenze utente
            models.Index(fields=['user', 'is_pinned'], name='user_pref_user_pinned_idx'),
        ]

    def __str__(self):
        pin_icon = "📌" if self.is_pinned else "📋"
        return f"{pin_icon} {self.user.get_full_name()} - {self.spending_plan.name}"


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

    PLAN_SCOPE_CHOICES = [
        ('family', 'Piano Familiare'),
        ('personal', 'Piano Personale'),
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
    plan_scope = models.CharField(
        max_length=10,
        choices=PLAN_SCOPE_CHOICES,
        default='family',
        verbose_name="Ambito piano",
        help_text="Familiare: condiviso con tutti i membri famiglia. Personale: visibile solo al creatore"
    )
    start_date = models.DateField(
        verbose_name="Data inizio",
        default='2025-09-01'
    )
    end_date = models.DateField(
        verbose_name="Data fine",
        default='2025-09-30'
    )
    total_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Budget totale pianificato",
        help_text="Budget complessivo pianificato per questo periodo"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='spending_plans',
        verbose_name="Utenti"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_spending_plans',
        verbose_name="Creato da",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Attivo"
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name="Nascosto",
        help_text="Se True, il piano non viene mostrato nelle liste principali"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Pinnati",
        help_text="Se True, il piano viene mostrato in cima e in evidenza"
    )
    auto_generated = models.BooleanField(
        default=False,
        verbose_name="Generato automaticamente",
        help_text="Indica se il piano è stato creato automaticamente da ricorrenze"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Piano Spese"
        verbose_name_plural = "Piani Spese"
        ordering = ['-is_pinned', '-start_date', '-created_at']

        # Indici per ottimizzare le query più comuni
        indexes = [
            # Indice per ordinamento e filtro temporale (usato in get_queryset)
            models.Index(fields=['-start_date', '-created_at'], name='spending_plan_date_idx'),

            # Indice per filtrare per scope e status attivo
            models.Index(fields=['plan_scope', 'is_active'], name='spending_plan_scope_active_idx'),

            # Indice per ordinamento con pin (usato in ordering)
            models.Index(fields=['-is_pinned', '-start_date'], name='spending_plan_pinned_idx'),

            # Indice per filtro piani nascosti
            models.Index(fields=['is_hidden', '-start_date'], name='spending_plan_hidden_idx'),
        ]

    def __str__(self):
        scope_icon = "👥" if self.plan_scope == 'family' else "👤"
        return f"{scope_icon} {self.name} ({self.start_date} - {self.end_date})"

    @property
    def is_family_plan(self):
        """Indica se è un piano familiare"""
        return self.plan_scope == 'family'

    @property
    def is_personal_plan(self):
        """Indica se è un piano personale"""
        return self.plan_scope == 'personal'

    @property
    def is_shared(self):
        """Retrocompatibilità per is_shared"""
        return self.plan_scope == 'family'

    def get_total_planned_amount(self):
        """Calcola l'importo totale pianificato"""
        return self.planned_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_total_unplanned_expenses_amount(self):
        """Calcola l'importo totale delle spese non pianificate collegate al piano"""
        from apps.expenses.models import Expense
        return Expense.objects.filter(
            spending_plan=self,
            status__in=['pagata', 'parzialmente_pagata']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    def get_total_estimated_amount(self):
        """Calcola l'importo totale stimato (pianificate + non pianificate)"""
        planned = self.get_total_planned_amount()
        unplanned = self.get_total_unplanned_expenses_amount()
        return planned + unplanned

    def get_completed_expenses_amount(self):
        """Calcola l'importo totale già pagato (pianificate + non pianificate)"""
        from apps.expenses.models import Expense

        # Importo pagato per spese pianificate (query diretta più efficiente)
        planned_paid = Expense.objects.filter(
            planned_expense__spending_plan=self
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Spese non pianificate pagate
        unplanned_completed = self.get_total_unplanned_expenses_amount()

        return planned_paid + unplanned_completed

    def get_completed_count(self):
        """Calcola il numero di spese completate/pagate (pianificate + non pianificate)"""
        from apps.expenses.models import Expense

        # Spese pianificate con payment_status='completed' (100% pagate)
        planned_count = 0
        for expense in self.planned_expenses.all():
            if expense.get_payment_status() == 'completed':
                planned_count += 1

        # Spese non pianificate pagate
        unplanned_count = Expense.objects.filter(
            spending_plan=self,
            status__in=['pagata', 'parzialmente_pagata']
        ).count()

        return planned_count + unplanned_count

    def get_total_expenses_count(self):
        """Calcola il numero totale di spese (pianificate + non pianificate)"""
        from apps.expenses.models import Expense

        planned_count = self.planned_expenses.count()
        unplanned_count = Expense.objects.filter(spending_plan=self).count()

        return planned_count + unplanned_count

    def get_pending_expenses_amount(self):
        """Calcola l'importo rimanente da pagare (differenza tra stimato e pagato)"""
        total_estimated = self.get_total_estimated_amount()
        total_paid = self.get_completed_expenses_amount()
        return max(total_estimated - total_paid, Decimal('0.00'))

    def get_completion_percentage(self):
        """Calcola la percentuale di completamento"""
        total_count = self.get_total_expenses_count()
        if total_count > 0:
            completed_count = self.get_completed_count()
            return (completed_count / total_count * 100)
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

    PAYMENT_TYPE_CHOICES = [
        ('shared', 'Condivisa'),
        ('partial', 'Parziale'),
        ('individual', 'Individuale'),
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
    is_hidden = models.BooleanField(
        default=False,
        verbose_name="Nascosta",
        help_text="Nascondi questa spesa dalla visualizzazione (utile per spese già pagate)"
    )
    actual_expense = models.ForeignKey(
        'expenses.Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Spesa reale",
        help_text="Spesa effettiva collegata a questa pianificazione"
    )
    # Campi per ricorrenza
    is_recurring = models.BooleanField(
        default=False,
        verbose_name="Spesa ricorrente"
    )
    total_installments = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Numero rate totali",
        help_text="Es: 10 per dentista in 10 rate"
    )
    installment_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Numero rata corrente"
    )
    parent_recurring_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ID gruppo ricorrenza",
        help_text="Identifica il gruppo di rate collegate"
    )
    recurring_frequency = models.CharField(
        max_length=20,
        choices=[('monthly', 'Mensile'), ('bimonthly', 'Bimestrale'), ('quarterly', 'Trimestrale')],
        default='monthly',
        null=True,
        blank=True,
        verbose_name="Frequenza ricorrenza"
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='shared',
        verbose_name="Tipo Pagamento",
        help_text="Indica se la spesa è condivisa, parziale o individuale"
    )
    my_share_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Mia Quota",
        help_text="Importo effettivamente pagato da me (solo per spese parziali)"
    )
    paid_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='individual_planned_expenses_paid',
        verbose_name="Pagata da",
        help_text="Utente che paga la spesa (solo per spese individuali)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Spesa Pianificata"
        verbose_name_plural = "Spese Pianificate"
        ordering = ['due_date', '-priority', 'created_at']

        # Indici per ottimizzare le query più comuni
        indexes = [
            # Indice per filtrare per piano e completamento (usato spesso nelle annotazioni)
            models.Index(fields=['spending_plan', 'is_completed'], name='planned_exp_plan_completed_idx'),

            # Indice per spese ricorrenti (lookup per parent_recurring_id)
            models.Index(fields=['parent_recurring_id', 'installment_number'], name='planned_exp_recurring_idx'),

            # Indice per ordinamento predefinito
            models.Index(fields=['due_date', '-priority'], name='planned_exp_due_priority_idx'),

            # Indice per spese nascoste
            models.Index(fields=['is_hidden', 'due_date'], name='planned_exp_hidden_idx'),
        ]

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

    def get_recurring_siblings(self):
        """Restituisce tutte le spese pianificate dello stesso gruppo ricorrente"""
        if not self.parent_recurring_id:
            return PlannedExpense.objects.none()
        return PlannedExpense.objects.filter(
            parent_recurring_id=self.parent_recurring_id
        ).order_by('installment_number')

    def get_next_installment(self):
        """Restituisce la prossima rata dello stesso gruppo"""
        if not self.parent_recurring_id:
            return None
        return PlannedExpense.objects.filter(
            parent_recurring_id=self.parent_recurring_id,
            installment_number=self.installment_number + 1
        ).first()

    def get_previous_installment(self):
        """Restituisce la rata precedente dello stesso gruppo"""
        if not self.parent_recurring_id or self.installment_number <= 1:
            return None
        return PlannedExpense.objects.filter(
            parent_recurring_id=self.parent_recurring_id,
            installment_number=self.installment_number - 1
        ).first()

    def is_first_installment(self):
        """Verifica se è la prima rata del gruppo"""
        return self.installment_number == 1

    def is_last_installment(self):
        """Verifica se è l'ultima rata del gruppo"""
        if not self.total_installments:
            return False
        return self.installment_number == self.total_installments

    def get_my_share(self):
        """Calcola la quota da pagare in base al payment_type"""
        from decimal import Decimal
        if self.payment_type == 'individual':
            # Spesa individuale: pago tutto
            return self.amount
        elif self.payment_type == 'partial':
            # Spesa parziale: uso my_share_amount se valorizzato, altrimenti metà
            if self.my_share_amount is not None:
                return self.my_share_amount
            return self.amount / 2
        else:
            # Spesa condivisa: nessuna quota specifica
            return Decimal('0.00')

    def get_other_share(self):
        """Calcola la quota dell'altra persona"""
        from decimal import Decimal
        if self.payment_type == 'partial':
            my_share = self.get_my_share()
            return self.amount - my_share
        return Decimal('0.00')


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

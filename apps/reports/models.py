from django.db import models
from django.conf import settings
from django.db.models import Sum, Count, Avg
from apps.categories.models import Category
from apps.expenses.models import Expense
from decimal import Decimal


class Budget(models.Model):
    """
    Modello per i budget famigliari
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nome budget"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrizione"
    )
    year = models.IntegerField(
        verbose_name="Anno"
    )
    month = models.IntegerField(
        verbose_name="Mese",
        choices=[(i, i) for i in range(1, 13)]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo totale"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='budgets',
        verbose_name="Utenti"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Attivo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budget"
        ordering = ['-year', '-month']
        unique_together = ['year', 'month', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.month}/{self.year}"
    
    def get_spent_amount(self):
        """Calcola l'importo speso per questo budget"""
        return Expense.objects.filter(
            user__in=self.users.all(),
            date__year=self.year,
            date__month=self.month,
            status='pagata'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    def get_remaining_amount(self):
        """Calcola l'importo rimanente del budget"""
        return self.total_amount - self.get_spent_amount()
    
    def get_percentage_used(self):
        """Calcola la percentuale di budget utilizzata"""
        spent = self.get_spent_amount()
        if self.total_amount > 0:
            return (spent / self.total_amount * 100)
        return Decimal('0.00')


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
            date__year=self.budget.year,
            date__month=self.budget.month,
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

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


class Contribution(models.Model):
    """
    Modello per gestire i contributi/depositi della famiglia
    """
    CONTRIBUTION_TYPE_CHOICES = [
        ('contanti', 'Contanti'),
        ('bonifico', 'Bonifico Ricevuto'),
        ('stipendio', 'Stipendio'),
        ('regalo', 'Regalo'),
        ('rimborso', 'Rimborso'),
        ('vendita', 'Vendita'),
        ('altro', 'Altro'),
    ]

    STATUS_CHOICES = [
        ('disponibile', 'Disponibile'),
        ('parzialmente_utilizzato', 'Parzialmente Utilizzato'),
        ('esaurito', 'Esaurito'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contributions',
        verbose_name="Utente che ha contribuito"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Importo contributo"
    )

    available_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Saldo disponibile",
        help_text="Importo ancora disponibile per le spese"
    )

    description = models.CharField(
        max_length=255,
        verbose_name="Descrizione"
    )

    contribution_type = models.CharField(
        max_length=20,
        choices=CONTRIBUTION_TYPE_CHOICES,
        default='contanti',
        verbose_name="Tipo di contributo"
    )

    date = models.DateField(
        default=timezone.now,
        verbose_name="Data contributo"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Note aggiuntive"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='disponibile',
        verbose_name="Stato"
    )

    family = models.ForeignKey(
        'users.Family',
        on_delete=models.CASCADE,
        related_name='contributions',
        verbose_name="Famiglia",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contributo"
        verbose_name_plural = "Contributi"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['user', '-date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.description} - €{self.amount} ({self.user.get_full_name() or self.user.username})"

    def save(self, *args, **kwargs):
        # Se è un nuovo contributo, il saldo disponibile è uguale all'importo
        if not self.pk:
            self.available_balance = self.amount

        # Aggiorna lo stato in base al saldo disponibile
        if self.available_balance == Decimal('0.00'):
            self.status = 'esaurito'
        elif self.available_balance < self.amount:
            self.status = 'parzialmente_utilizzato'
        else:
            self.status = 'disponibile'

        super().save(*args, **kwargs)

    def use_amount(self, amount):
        """
        Utilizza una parte del contributo per una spesa
        """
        if amount > self.available_balance:
            raise ValueError(f"Importo richiesto ({amount}) superiore al saldo disponibile ({self.available_balance})")

        self.available_balance -= amount
        self.save()

        return self.available_balance

    def restore_amount(self, amount):
        """
        Ripristina un importo precedentemente utilizzato (es. quando una spesa viene eliminata)
        """
        self.available_balance = min(self.available_balance + amount, self.amount)
        self.save()

        return self.available_balance

    def get_used_amount(self):
        """
        Calcola l'importo già utilizzato
        """
        return self.amount - self.available_balance

    def get_usage_percentage(self):
        """
        Calcola la percentuale di utilizzo
        """
        if self.amount > 0:
            return float((self.get_used_amount() / self.amount) * 100)
        return 0.0

    def get_related_expenses(self):
        """
        Restituisce tutte le spese collegate a questo contributo
        """
        from apps.expenses.models import Expense
        return Expense.objects.filter(
            expense_contributions__contribution=self
        ).distinct()

    def get_total_expenses_amount(self):
        """
        Calcola il totale delle spese pagate con questo contributo
        """
        total = self.expense_contributions.aggregate(
            total=models.Sum('amount_used')
        )['total'] or Decimal('0.00')
        return total


class ExpenseContribution(models.Model):
    """
    Modello di collegamento tra Spese e Contributi
    Traccia quanto di ogni contributo viene utilizzato per una spesa
    """
    expense = models.ForeignKey(
        'expenses.Expense',
        on_delete=models.CASCADE,
        related_name='expense_contributions',
        verbose_name="Spesa"
    )

    contribution = models.ForeignKey(
        Contribution,
        on_delete=models.PROTECT,
        related_name='expense_contributions',
        verbose_name="Contributo"
    )

    amount_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Importo utilizzato"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilizzo Contributo"
        verbose_name_plural = "Utilizzi Contributi"
        ordering = ['-created_at']
        unique_together = ['expense', 'contribution']

    def __str__(self):
        return f"€{self.amount_used} da {self.contribution.description} per {self.expense.description}"

    def save(self, *args, **kwargs):
        # Verifica che l'importo sia disponibile nel contributo
        if not self.pk:  # Solo per nuovi record
            if self.amount_used > self.contribution.available_balance:
                raise ValueError(
                    f"Importo richiesto ({self.amount_used}) superiore "
                    f"al saldo disponibile del contributo ({self.contribution.available_balance})"
                )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Ripristina l'importo nel contributo quando viene eliminato il collegamento
        self.contribution.restore_amount(self.amount_used)
        super().delete(*args, **kwargs)


class FamilyBalance(models.Model):
    """
    Modello per tracciare il saldo complessivo della famiglia
    """
    family = models.OneToOneField(
        'users.Family',
        on_delete=models.CASCADE,
        related_name='balance',
        verbose_name="Famiglia"
    )

    total_contributions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Totale contributi"
    )

    total_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Totale spese da contributi"
    )

    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo attuale"
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Ultimo aggiornamento"
    )

    class Meta:
        verbose_name = "Saldo Famiglia"
        verbose_name_plural = "Saldi Famiglie"

    def __str__(self):
        return f"Saldo {self.family.name}: €{self.current_balance}"

    def update_balance(self):
        """
        Aggiorna il saldo calcolando contributi e spese
        """
        from django.db.models import Sum

        # Calcola totale contributi
        self.total_contributions = self.family.contributions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Calcola totale utilizzato dai contributi
        self.total_expenses = self.family.contributions.aggregate(
            total=Sum('expense_contributions__amount_used')
        )['total'] or Decimal('0.00')

        # Calcola saldo attuale
        self.current_balance = self.family.contributions.aggregate(
            total=Sum('available_balance')
        )['total'] or Decimal('0.00')

        self.save()
        return self.current_balance

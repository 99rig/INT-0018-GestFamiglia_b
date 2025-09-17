from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    """
    Modello per le categorie di spese
    """
    CATEGORY_TYPE_CHOICES = [
        ('necessaria', 'Necessaria'),
        ('extra', 'Extra'),
    ]
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nome categoria"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrizione"
    )
    type = models.CharField(
        max_length=20, 
        choices=CATEGORY_TYPE_CHOICES,
        default='necessaria',
        verbose_name="Tipo di spesa"
    )
    icon = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Icona",
        help_text="Nome dell'icona da visualizzare"
    )
    color = models.CharField(
        max_length=7, 
        blank=True,
        verbose_name="Colore",
        help_text="Colore in formato HEX (es. #FF5733)"
    )
    monthly_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Budget mensile"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Attiva"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorie"
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Subcategory(models.Model):
    """
    Modello per le sottocategorie di spese
    """
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='subcategories',
        verbose_name="Categoria"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nome sottocategoria"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrizione"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Attiva"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sottocategoria"
        verbose_name_plural = "Sottocategorie"
        ordering = ['category', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

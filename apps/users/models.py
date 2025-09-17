from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager personalizzato per User con login via email"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'indirizzo email è obbligatorio')
        email = self.normalize_email(email)
        
        # Se username non è fornito, usa la parte locale dell'email
        if 'username' not in extra_fields:
            extra_fields['username'] = email.split('@')[0]
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Il superuser deve avere is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Il superuser deve avere is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modello utente personalizzato per la gestione degli utenti famigliari
    Login via email invece che username
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    objects = UserManager()
    
    email = models.EmailField(unique=True, verbose_name="Email")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        ordering = ['email']
    
    def __str__(self):
        return f"{self.get_full_name() or self.email}"


class UserProfile(models.Model):
    """
    Profilo utente con informazioni aggiuntive
    """
    ROLE_CHOICES = [
        ('master', 'Master (Genitore)'),
        ('familiare', 'Familiare'),
    ]
    
    FAMILY_ROLE_CHOICES = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('figlio', 'Figlio/a'),
        ('altro', 'Altro'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Utente"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='familiare',
        verbose_name="Ruolo sistema",
        help_text="Master può pianificare spese, Familiare può solo inserire spese"
    )
    family_role = models.CharField(
        max_length=20, 
        choices=FAMILY_ROLE_CHOICES, 
        default='altro',
        verbose_name="Ruolo in famiglia"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Numero di telefono"
    )
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Data di nascita"
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        verbose_name="Foto profilo"
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Biografia",
        help_text="Breve descrizione"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profilo Utente"
        verbose_name_plural = "Profili Utenti"
        ordering = ['role', 'family_role']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.get_role_display()}"
    
    @property
    def is_master(self):
        """Verifica se l'utente è un master"""
        return self.role == 'master'
    
    @property
    def can_plan_budget(self):
        """Verifica se può pianificare budget"""
        return self.is_master

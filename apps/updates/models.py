from django.db import models
from django.utils import timezone


class AppVersion(models.Model):
    """Modello per gestire le versioni dell'app"""
    
    version_name = models.CharField(max_length=20, help_text="es. 1.0.0")
    version_code = models.IntegerField(unique=True, help_text="Numero versione incrementale")
    apk_file = models.FileField(upload_to='apk/', help_text="File APK")
    release_notes = models.TextField(blank=True, help_text="Note di rilascio")
    is_mandatory = models.BooleanField(default=False, help_text="Aggiornamento obbligatorio")
    min_supported_version = models.IntegerField(help_text="Versione minima supportata")
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-version_code']
        verbose_name = "Versione App"
        verbose_name_plural = "Versioni App"
    
    def __str__(self):
        return f"v{self.version_name} ({self.version_code})"
    
    @classmethod
    def get_latest_version(cls):
        """Ritorna l'ultima versione disponibile"""
        return cls.objects.first()
    
    def is_newer_than(self, version_code):
        """Controlla se questa versione è più nuova"""
        return self.version_code > version_code
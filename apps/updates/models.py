import os
from django.db import models
from django.utils import timezone
from django.conf import settings


def apk_upload_path(instance, filename):
    """Definisce il percorso di upload per gli APK"""
    # Usa la configurazione APK_ROOT dai settings
    apk_dir = settings.APK_ROOT
    os.makedirs(apk_dir, exist_ok=True)

    # Estrae solo il nome del file per evitare path traversal
    safe_filename = os.path.basename(filename)
    return os.path.join('apk_releases', safe_filename)


class AppVersion(models.Model):
    """Modello per gestire le versioni dell'app"""
    
    version_name = models.CharField(max_length=20, help_text="es. 1.0.0")
    version_code = models.IntegerField(unique=True, help_text="Numero versione incrementale")
    apk_file = models.FileField(upload_to=apk_upload_path, help_text="File APK")
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

    @property
    def apk_file_path(self):
        """Ritorna il percorso corretto del file APK nella cartella apk_releases"""
        if self.apk_file:
            # Usa il percorso configurato in settings
            filename = os.path.basename(str(self.apk_file))
            return os.path.join(settings.APK_ROOT, filename)
        return None

    @property
    def apk_file_size(self):
        """Ritorna la dimensione del file APK"""
        apk_path = self.apk_file_path
        if apk_path and os.path.exists(apk_path):
            return os.path.getsize(apk_path)
        return 0

    def save(self, *args, **kwargs):
        """Override save per pulire automaticamente vecchie versioni"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Se è una nuova versione, pulisci le vecchie
        if is_new:
            self.cleanup_old_versions()

    @classmethod
    def cleanup_old_versions(cls, keep_count=5):
        """Mantiene solo le ultime N versioni, eliminando le più vecchie"""
        all_versions = cls.objects.order_by('-version_code')

        if all_versions.count() > keep_count:
            versions_to_delete = all_versions[keep_count:]

            for version in versions_to_delete:
                # Elimina file APK se esiste
                if version.apk_file_path and os.path.exists(version.apk_file_path):
                    try:
                        os.remove(version.apk_file_path)
                    except Exception as e:
                        print(f"Errore eliminando APK {version.apk_file_path}: {e}")

                # Elimina record
                version.delete()
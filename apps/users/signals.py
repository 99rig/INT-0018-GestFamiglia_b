from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea automaticamente un UserProfile quando viene creato un nuovo User
    """
    if created:
        UserProfile.objects.create(
            user=instance,
            role='master' if instance.is_superuser else 'familiare',
            family_role='altro'
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva il profilo quando viene salvato l'utente
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Se il profilo non esiste, lo crea
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'role': 'master' if instance.is_superuser else 'familiare',
                'family_role': 'altro'
            }
        )
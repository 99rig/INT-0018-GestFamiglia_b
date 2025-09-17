from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix missing user profiles'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            try:
                # Prova ad accedere al profilo
                profile = user.profile
                self.stdout.write(f"User {user.email} already has profile: {profile.role}")
            except UserProfile.DoesNotExist:
                # Crea il profilo mancante
                UserProfile.objects.create(
                    user=user,
                    role='master' if user.is_superuser else 'familiare',
                    family_role='altro'
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created profile for user {user.email}")
                )
        
        if created_count == 0:
            self.stdout.write(self.style.SUCCESS("All users already have profiles"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Created {created_count} missing profiles")
            )
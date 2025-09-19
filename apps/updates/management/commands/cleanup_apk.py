from django.core.management.base import BaseCommand
from django.conf import settings
from apps.updates.models import AppVersion
import os


class Command(BaseCommand):
    help = 'Pulisce le vecchie versioni APK mantenendo solo le ultime N versioni'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=5,
            help='Numero di versioni da mantenere (default: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe eliminato senza farlo realmente'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Elimina senza chiedere conferma'
        )

    def handle(self, *args, **options):
        keep_count = options['keep']
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(f"Mantenendo le ultime {keep_count} versioni...")

        # Ottieni tutte le versioni ordinate per version_code decrescente
        all_versions = AppVersion.objects.order_by('-version_code')
        total_count = all_versions.count()

        if total_count <= keep_count:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Ci sono solo {total_count} versioni, niente da pulire."
                )
            )
            return

        # Versioni da mantenere
        versions_to_keep = all_versions[:keep_count]
        # Versioni da eliminare
        versions_to_delete = all_versions[keep_count:]

        self.stdout.write("\nVersioni da MANTENERE:")
        for v in versions_to_keep:
            file_size = v.apk_file_size / (1024 * 1024)  # Convert to MB
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ v{v.version_name} ({v.version_code}) - {file_size:.1f}MB")
            )

        self.stdout.write("\nVersioni da ELIMINARE:")
        total_space_freed = 0
        for v in versions_to_delete:
            file_size = v.apk_file_size / (1024 * 1024)  # Convert to MB
            total_space_freed += v.apk_file_size
            self.stdout.write(
                self.style.WARNING(f"  ✗ v{v.version_name} ({v.version_code}) - {file_size:.1f}MB")
            )

        total_space_mb = total_space_freed / (1024 * 1024)
        self.stdout.write(
            f"\nSpazio che verrà liberato: {total_space_mb:.1f}MB"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n--dry-run: Nessun file è stato eliminato")
            )
            return

        # Chiedi conferma se non in modalità force
        if not force:
            confirm = input(
                f"\nVuoi eliminare {versions_to_delete.count()} versioni vecchie? [y/N]: "
            )
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR("Operazione annullata"))
                return

        # Elimina file APK e record database
        deleted_count = 0
        for version in versions_to_delete:
            try:
                # Elimina file APK se esiste
                if version.apk_file_path and os.path.exists(version.apk_file_path):
                    os.remove(version.apk_file_path)
                    self.stdout.write(
                        f"  Eliminato file: {os.path.basename(version.apk_file_path)}"
                    )

                # Elimina record dal database
                version_info = f"v{version.version_name}"
                version.delete()
                deleted_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Eliminata versione {version_info} dal database")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Errore eliminando v{version.version_name}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Eliminate {deleted_count} versioni, liberati {total_space_mb:.1f}MB"
            )
        )
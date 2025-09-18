from django.core.management.base import BaseCommand
from apps.categories.models import Category


class Command(BaseCommand):
    help = 'Aggiorna le icone delle categorie con Material Design Icons'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe aggiornato senza salvare nel database',
        )

    def handle(self, *args, **options):
        # Mappatura delle icone ottimizzate con Material Design Icons
        ICON_MAP = {
            # Categorie Necessarie
            'Casa e Abitazione': 'home',
            'Alimentari e Bevande': 'shopping_cart',
            'Trasporti': 'directions_car',
            'Salute e Benessere': 'local_hospital',
            'Assicurazioni': 'security',
            'Tasse e Imposte': 'receipt_long',
            'Educazione e Formazione': 'school',

            # Categorie Extra
            'Tempo Libero': 'movie',
            'Viaggi e Vacanze': 'flight',
            'Abbigliamento': 'checkroom',
            'Elettronica e Tecnologia': 'devices',
            'Casa Extra': 'home_repair_service',
            'Sport e Fitness': 'fitness_center',
            'Regali e Eventi': 'card_giftcard',
            'Animali Domestici': 'pets',
        }

        updated_count = 0

        for category_name, icon_name in ICON_MAP.items():
            try:
                category = Category.objects.get(name=category_name)

                if not options['dry_run']:
                    old_icon = category.icon
                    category.icon = icon_name
                    category.save()
                    updated_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Aggiornato "{category_name}": {old_icon} → {icon_name}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[DRY RUN] Aggiornerei "{category_name}": {category.icon} → {icon_name}'
                        )
                    )

            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Categoria "{category_name}" non trovata, salto...'
                    )
                )

        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Completato! Aggiornate {updated_count} categorie con nuove icone Material Design.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Aggiornerei {len(ICON_MAP)} categorie con nuove icone Material Design.'
                )
            )
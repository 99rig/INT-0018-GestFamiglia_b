from django.core.management.base import BaseCommand
from apps.categories.models import Category, Subcategory


class Command(BaseCommand):
    help = 'Aggiunge icone specifiche alle sottocategorie più importanti'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe aggiornato senza salvare nel database',
        )

    def handle(self, *args, **options):
        # Mappatura delle icone per sottocategorie specifiche
        SUBCATEGORY_ICONS = {
            # Trasporti
            'Carburante': 'local_gas_station',
            'Mezzi Pubblici': 'directions_bus',
            'Manutenzione Auto': 'build',
            'Assicurazione Auto': 'shield',
            'Parcheggi': 'local_parking',
            'Pedaggi Autostradali': 'toll',
            'Taxi/Uber': 'local_taxi',

            # Alimentari e Bevande
            'Spesa Quotidiana': 'shopping_basket',
            'Panetteria': 'bakery_dining',
            'Macelleria/Pescheria': 'restaurant',
            'Frutta e Verdura': 'eco',
            'Bevande': 'local_bar',

            # Salute e Benessere
            'Farmaci': 'medication',
            'Visite Mediche': 'medical_services',
            'Dentista': 'dentistry',
            'Oculista': 'visibility',
            'Analisi Cliniche': 'science',

            # Casa e Abitazione
            'Affitto/Mutuo': 'home',
            'Bolletta Luce': 'electrical_services',
            'Bolletta Gas': 'local_fire_department',
            'Bolletta Acqua': 'water_drop',
            'Internet/Telefono': 'wifi',
            'Manutenzione Casa': 'handyman',

            # Educazione e Formazione
            'Retta Scolastica': 'school',
            'Mensa Scolastica': 'restaurant_menu',
            'Libri Scolastici': 'menu_book',
            'Materiale Scolastico': 'edit',
            'Università': 'account_balance',

            # Tempo Libero
            'Cinema e Teatro': 'theaters',
            'Ristoranti e Bar': 'restaurant',
            'Hobby': 'palette',
            'Streaming (Netflix, ecc)': 'play_circle',

            # Sport e Fitness
            'Palestra': 'fitness_center',
            'Attrezzature Sportive': 'sports_tennis',

            # Viaggi e Vacanze
            'Vacanze Estive': 'beach_access',
            'Biglietti Aerei/Treni': 'confirmation_number',
            'Hotel e Alloggi': 'hotel',

            # Abbigliamento
            'Vestiti Adulti': 'checkroom',
            'Scarpe': 'style',

            # Elettronica e Tecnologia
            'Smartphone': 'smartphone',
            'Computer e Tablet': 'computer',
            'Elettrodomestici': 'kitchen',

            # Animali Domestici
            'Cibo per Animali': 'pet_supplies',
            'Veterinario': 'pets',
            'Accessori Animali': 'pets',

            # Regali e Eventi
            'Compleanni': 'cake',
            'Natale': 'celebration',
            'Matrimoni': 'favorite',
        }

        updated_count = 0

        for subcategory_name, icon_name in SUBCATEGORY_ICONS.items():
            try:
                subcategory = Subcategory.objects.get(name=subcategory_name)

                if not options['dry_run']:
                    old_icon = subcategory.icon if subcategory.icon else 'nessuna'
                    subcategory.icon = icon_name
                    subcategory.save()
                    updated_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Aggiornato "{subcategory_name}": {old_icon} → {icon_name}'
                        )
                    )
                else:
                    current_icon = subcategory.icon if subcategory.icon else 'nessuna'
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[DRY RUN] Aggiornerei "{subcategory_name}": {current_icon} → {icon_name}'
                        )
                    )

            except Subcategory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Sottocategoria "{subcategory_name}" non trovata, salto...'
                    )
                )

        if not options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Completato! Aggiornate {updated_count} sottocategorie con icone specifiche.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Aggiornerei {len(SUBCATEGORY_ICONS)} sottocategorie con icone specifiche.'
                )
            )
from django.core.management.base import BaseCommand, CommandError
from categories.models import Category, Subcategory


class Command(BaseCommand):
    help = 'Popola il database con categorie e sottocategorie predefinite per famiglie italiane'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina tutte le categorie esistenti prima di creare quelle nuove',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe creato senza salvare nel database',
        )

    def handle(self, *args, **options):
        if options['clear']:
            if not options['dry_run']:
                Category.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING('Eliminate tutte le categorie esistenti.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('[DRY RUN] Eliminerei tutte le categorie esistenti.')
                )

        # Definizione categorie necessarie
        necessary_categories = {
            'Casa e Abitazione': {
                'description': 'Spese per l\'abitazione principale',
                'icon': 'home',
                'color': '#2196F3',
                'monthly_budget': 1200.00,
                'subcategories': [
                    'Affitto/Mutuo',
                    'Bolletta Luce',
                    'Bolletta Gas',
                    'Bolletta Acqua',
                    'Internet/Telefono',
                    'Rifiuti (TARI)',
                    'Manutenzione Casa',
                    'Spese Condominiali'
                ]
            },
            'Alimentari e Bevande': {
                'description': 'Spese per cibo e bevande essenziali',
                'icon': 'shopping-cart',
                'color': '#4CAF50',
                'monthly_budget': 600.00,
                'subcategories': [
                    'Spesa Quotidiana',
                    'Panetteria',
                    'Macelleria/Pescheria',
                    'Frutta e Verdura',
                    'Bevande',
                    'Prodotti per Neonati',
                    'Prodotti Biologici'
                ]
            },
            'Trasporti': {
                'description': 'Spese per mobilità e trasporti',
                'icon': 'car',
                'color': '#FF9800',
                'monthly_budget': 300.00,
                'subcategories': [
                    'Carburante',
                    'Mezzi Pubblici',
                    'Manutenzione Auto',
                    'Assicurazione Auto',
                    'Bollo Auto',
                    'Parcheggi',
                    'Pedaggi Autostradali',
                    'Taxi/Uber'
                ]
            },
            'Salute e Benessere': {
                'description': 'Spese mediche e per la salute',
                'icon': 'medical-bag',
                'color': '#F44336',
                'monthly_budget': 200.00,
                'subcategories': [
                    'Farmaci',
                    'Visite Mediche',
                    'Dentista',
                    'Oculista',
                    'Analisi Cliniche',
                    'Fisioterapia',
                    'Prodotti Sanitari'
                ]
            },
            'Assicurazioni': {
                'description': 'Polizze assicurative obbligatorie',
                'icon': 'shield',
                'color': '#607D8B',
                'monthly_budget': 150.00,
                'subcategories': [
                    'Assicurazione Casa',
                    'Assicurazione Vita',
                    'Assicurazione Sanitaria',
                    'Assicurazione Infortuni'
                ]
            },
            'Tasse e Imposte': {
                'description': 'Imposte e tasse obbligatorie',
                'icon': 'receipt',
                'color': '#795548',
                'monthly_budget': 400.00,
                'subcategories': [
                    'IRPEF',
                    'IMU',
                    'TASI',
                    'Canone RAI',
                    'Altre Imposte'
                ]
            },
            'Educazione e Formazione': {
                'description': 'Spese per istruzione e formazione',
                'icon': 'school',
                'color': '#3F51B5',
                'monthly_budget': 250.00,
                'subcategories': [
                    'Retta Scolastica',
                    'Mensa Scolastica',
                    'Libri Scolastici',
                    'Materiale Scolastico',
                    'Università',
                    'Corsi di Formazione',
                    'Ripetizioni'
                ]
            }
        }

        # Definizione categorie extra
        extra_categories = {
            'Tempo Libero': {
                'description': 'Attività ricreative e divertimento',
                'icon': 'entertainment',
                'color': '#E91E63',
                'monthly_budget': 200.00,
                'subcategories': [
                    'Cinema e Teatro',
                    'Ristoranti e Bar',
                    'Hobby',
                    'Libri e Riviste',
                    'Streaming (Netflix, ecc)',
                    'Concerti ed Eventi',
                    'Giochi e Videogiochi'
                ]
            },
            'Viaggi e Vacanze': {
                'description': 'Viaggi, vacanze e weekend',
                'icon': 'airplane',
                'color': '#00BCD4',
                'monthly_budget': 300.00,
                'subcategories': [
                    'Vacanze Estive',
                    'Weekend Fuori',
                    'Biglietti Aerei/Treni',
                    'Hotel e Alloggi',
                    'Escursioni',
                    'Souvenir'
                ]
            },
            'Abbigliamento': {
                'description': 'Vestiti, scarpe e accessori',
                'icon': 'shirt',
                'color': '#9C27B0',
                'monthly_budget': 150.00,
                'subcategories': [
                    'Vestiti Adulti',
                    'Vestiti Bambini',
                    'Scarpe',
                    'Accessori',
                    'Abbigliamento Stagionale',
                    'Intimo'
                ]
            },
            'Elettronica e Tecnologia': {
                'description': 'Dispositivi elettronici e tecnologia',
                'icon': 'computer',
                'color': '#673AB7',
                'monthly_budget': 100.00,
                'subcategories': [
                    'Smartphone',
                    'Computer e Tablet',
                    'Elettrodomestici',
                    'Accessori Tech',
                    'Software',
                    'Riparazioni'
                ]
            },
            'Casa Extra': {
                'description': 'Arredamento e miglioramenti casa',
                'icon': 'home-improvement',
                'color': '#8BC34A',
                'monthly_budget': 100.00,
                'subcategories': [
                    'Arredamento',
                    'Decorazioni',
                    'Giardinaggio',
                    'Attrezzi',
                    'Biancheria Casa',
                    'Prodotti Pulizia Extra'
                ]
            },
            'Sport e Fitness': {
                'description': 'Attività sportive e fitness',
                'icon': 'fitness',
                'color': '#FF5722',
                'monthly_budget': 80.00,
                'subcategories': [
                    'Palestra',
                    'Attrezzature Sportive',
                    'Abbigliamento Sportivo',
                    'Lezioni/Corsi Sport',
                    'Integratori'
                ]
            },
            'Regali e Eventi': {
                'description': 'Regali e eventi speciali',
                'icon': 'gift',
                'color': '#FFC107',
                'monthly_budget': 100.00,
                'subcategories': [
                    'Compleanni',
                    'Natale',
                    'Anniversari',
                    'Eventi Speciali',
                    'Matrimoni',
                    'Baby Shower'
                ]
            },
            'Animali Domestici': {
                'description': 'Spese per animali domestici',
                'icon': 'pets',
                'color': '#CDDC39',
                'monthly_budget': 50.00,
                'subcategories': [
                    'Cibo per Animali',
                    'Veterinario',
                    'Accessori Animali',
                    'Toelettatura',
                    'Farmaci Animali'
                ]
            }
        }

        self._create_categories(necessary_categories, 'necessaria', options['dry_run'])
        self._create_categories(extra_categories, 'extra', options['dry_run'])

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS('[DRY RUN] Anteprima completata. Usa il comando senza --dry-run per salvare.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Categorie e sottocategorie predefinite create con successo!')
            )

    def _create_categories(self, categories_data, category_type, dry_run):
        """Crea le categorie del tipo specificato"""
        
        for cat_name, cat_data in categories_data.items():
            if dry_run:
                self.stdout.write(f'[DRY RUN] Creerei categoria: {cat_name} ({category_type})')
            else:
                # Crea o aggiorna la categoria
                category, created = Category.objects.get_or_create(
                    name=cat_name,
                    defaults={
                        'description': cat_data['description'],
                        'type': category_type,
                        'icon': cat_data['icon'],
                        'color': cat_data['color'],
                        'monthly_budget': cat_data['monthly_budget'],
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Creata categoria: {cat_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'→ Categoria già esistente: {cat_name}')
                    )

            # Crea le sottocategorie
            for subcat_name in cat_data['subcategories']:
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Creerei sottocategoria: {subcat_name}')
                else:
                    subcategory, created = Subcategory.objects.get_or_create(
                        category=category,
                        name=subcat_name,
                        defaults={
                            'description': f'Sottocategoria per {subcat_name.lower()}',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'  ✓ Creata sottocategoria: {subcat_name}')
                    else:
                        self.stdout.write(f'  → Sottocategoria già esistente: {subcat_name}')
from django.core.management.base import BaseCommand
from apps.categories.models import Category, Subcategory


class Command(BaseCommand):
    help = 'Popola gli alias per le sottocategorie per migliorare la ricerca'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Rimuove tutti gli alias esistenti prima di aggiungere quelli nuovi',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe creato senza salvare nel database',
        )

    def handle(self, *args, **options):
        # Mappatura degli alias per sottocategorie
        ALIASES_MAP = {
            # Trasporti
            'Carburante': ['benzina', 'gasolio', 'diesel', 'gpl', 'metano', 'gas', 'rifornimento'],
            'Mezzi Pubblici': ['autobus', 'bus', 'metro', 'metropolitana', 'treno', 'tram', 'atac', 'atm'],
            'Finanziamento Auto': ['rata auto', 'rata macchina', 'rata', 'finanziamento', 'prestito auto', 'leasing'],
            'Manutenzione Auto': ['meccanico', 'tagliando', 'revisione', 'gomme', 'pneumatici', 'olio'],
            'Parcheggi': ['parcheggio', 'garage', 'box', 'sosta'],
            'Pedaggi Autostradali': ['casello', 'telepass', 'viacard', 'autostrada'],
            'Taxi/Uber': ['taxi', 'uber', 'corsa', 'ride'],

            # Alimentari e Bevande
            'Spesa Quotidiana': ['spesa', 'supermercato', 'conad', 'coop', 'esselunga', 'carrefour', 'eurospin'],
            'Panetteria': ['pane', 'panificio', 'cornetti', 'brioche', 'focaccia'],
            'Macelleria/Pescheria': ['carne', 'pesce', 'salumi', 'macellaio', 'pescivendolo'],
            'Frutta e Verdura': ['frutta', 'verdura', 'ortofrutta', 'fruttivendolo'],
            'Bevande': ['vino', 'birra', 'acqua', 'bibite', 'caffè'],

            # Casa e Abitazione
            'Affitto/Mutuo': ['affitto', 'mutuo', 'canone', 'rata'],
            'Bolletta Luce': ['luce', 'elettricità', 'enel', 'energia elettrica'],
            'Bolletta Gas': ['gas', 'eni', 'metano', 'riscaldamento'],
            'Bolletta Acqua': ['acqua', 'idrica', 'acea'],
            'Internet/Telefono': ['internet', 'telefono', 'adsl', 'fibra', 'tim', 'vodafone', 'wind'],
            'Manutenzione Casa': ['idraulico', 'elettricista', 'imbianchino', 'riparazioni'],

            # Salute e Benessere
            'Farmaci': ['medicina', 'medicinali', 'farmacia', 'pastiglie', 'sciroppo'],
            'Visite Mediche': ['dottore', 'medico', 'visita', 'specialista'],
            'Dentista': ['denti', 'dentale', 'ortodonzia', 'pulizia denti'],
            'Oculista': ['occhi', 'vista', 'oculare', 'lenti'],
            'Analisi Cliniche': ['analisi', 'esami', 'laboratorio', 'prelievo'],

            # Educazione e Formazione
            'Retta Scolastica': ['scuola', 'retta', 'iscrizione', 'tasse scolastiche'],
            'Mensa Scolastica': ['mensa', 'pranzo scuola'],
            'Libri Scolastici': ['libri', 'testi', 'manuale'],
            'Materiale Scolastico': ['quaderni', 'penne', 'matite', 'zaino', 'cartoleria'],
            'Università': ['uni', 'università', 'facoltà', 'corso di laurea'],

            # Tempo Libero
            'Cinema/Teatro': ['cinema', 'teatro', 'film', 'spettacolo'],
            'Ristoranti': ['ristorante', 'pizzeria', 'trattoria', 'cena fuori'],
            'Bar/Aperitivi': ['bar', 'aperitivo', 'drink', 'cocktail'],
            'Hobby': ['hobby', 'passatempo', 'bricolage'],

            # Sport e Fitness
            'Palestra': ['gym', 'fitness', 'allenamento'],
            'Piscina': ['nuoto', 'swimming'],

            # Abbigliamento
            'Vestiti': ['vestiti', 'abbigliamento', 'magliette', 'pantaloni'],
            'Scarpe': ['calzature', 'sneakers', 'sandali'],

            # Animali Domestici
            'Cibo per Animali': ['crocchette', 'scatolette', 'mangime', 'cibo cane', 'cibo gatto'],
            'Veterinario': ['vet', 'veterinario', 'vaccinazioni'],
            'Accessori Animali': ['guinzaglio', 'collare', 'giochi', 'cuccia'],
            'Farmaci Animali': ['antiparassitari', 'vermifugo', 'medicine animali'],
            'Toelettatura': ['bagno cane', 'taglio unghie', 'spazzolatura'],
        }

        if options['clear']:
            if not options['dry_run']:
                Subcategory.objects.all().update(aliases=[])
                self.stdout.write(
                    self.style.WARNING('Rimossi tutti gli alias esistenti.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('[DRY RUN] Rimuoverei tutti gli alias esistenti.')
                )

        updated_count = 0
        created_count = 0

        for subcategory_name, aliases in ALIASES_MAP.items():
            try:
                subcategory = Subcategory.objects.get(name=subcategory_name)

                if not options['dry_run']:
                    subcategory.aliases = aliases
                    subcategory.save()
                    updated_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[DRY RUN] " if options["dry_run"] else ""}'
                        f'Aggiornato "{subcategory_name}" con alias: {", ".join(aliases)}'
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
                    f'\n✅ Completato! Aggiornate {updated_count} sottocategorie con alias.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY RUN] Aggiornerei {len(ALIASES_MAP)} sottocategorie con alias.'
                )
            )
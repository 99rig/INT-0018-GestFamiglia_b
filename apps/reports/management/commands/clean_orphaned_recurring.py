from django.core.management.base import BaseCommand
from django.db import transaction
from apps.reports.models import PlannedExpense, SpendingPlan


class Command(BaseCommand):
    help = 'Pulisce le rate ricorrenti orfane (senza piano di spesa)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe fatto senza modificare il database',
        )
        parser.add_argument(
            '--reset-parent-id',
            action='store_true',
            help='Reset parent_recurring_id per permettere rigenerazione',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        reset_parent = options['reset_parent_id']

        self.stdout.write(self.style.SUCCESS('=== PULIZIA RATE RICORRENTI ORFANE ==='))

        # Trova tutti i gruppi di spese ricorrenti
        parent_ids = PlannedExpense.objects.exclude(
            parent_recurring_id__isnull=True
        ).exclude(
            parent_recurring_id=''
        ).values_list('parent_recurring_id', flat=True).distinct()

        total_deleted = 0
        total_reset = 0

        for parent_id in parent_ids:
            group = PlannedExpense.objects.filter(parent_recurring_id=parent_id)

            # Trova rate orfane (senza piano)
            orphaned = group.filter(spending_plan__isnull=True)
            with_plan = group.filter(spending_plan__isnull=False)

            if orphaned.exists():
                self.stdout.write(f'\nGruppo {parent_id[:8]}...:')
                self.stdout.write(f'  - Rate totali: {group.count()}')
                self.stdout.write(f'  - Con piano: {with_plan.count()}')
                self.stdout.write(f'  - ORFANE (senza piano): {orphaned.count()}')

                if not dry_run:
                    # Cancella le rate orfane
                    deleted = orphaned.delete()
                    total_deleted += deleted[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Eliminate {deleted[0]} rate orfane'))
                else:
                    self.stdout.write(self.style.WARNING(f'  [DRY-RUN] Eliminerebbero {orphaned.count()} rate orfane'))

            # Se richiesto, reset del parent_id sulla prima rata per permettere rigenerazione
            if reset_parent and with_plan.exists():
                first_installment = with_plan.order_by('id').first()
                if first_installment and first_installment.total_installments:
                    actual_count = with_plan.count()
                    expected_count = first_installment.total_installments

                    if actual_count < expected_count:
                        self.stdout.write(f'\nGruppo {parent_id[:8]}... necessita rigenerazione:')
                        self.stdout.write(f'  - Rate esistenti: {actual_count}')
                        self.stdout.write(f'  - Rate previste: {expected_count}')

                        if not dry_run:
                            # Reset parent_id sulla prima rata per permettere rigenerazione
                            first_installment.parent_recurring_id = None
                            first_installment.save(update_fields=['parent_recurring_id'])
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Reset parent_id su ID {first_installment.id}'))
                            total_reset += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'  [DRY-RUN] Reset parent_id su ID {first_installment.id}'))

        # Trova spese ricorrenti isolate (is_recurring=True ma senza parent_id)
        isolated = PlannedExpense.objects.filter(
            is_recurring=True,
            parent_recurring_id__isnull=True
        )

        if isolated.exists():
            self.stdout.write(f'\n=== SPESE RICORRENTI ISOLATE ===')
            for expense in isolated:
                self.stdout.write(f'  ID {expense.id}: {expense.description} - Rate: {expense.total_installments}')
                if reset_parent:
                    self.stdout.write(self.style.SUCCESS('    → Pronta per rigenerazione'))

        # Riassunto finale
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN MODE] Nessuna modifica effettuata'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Rate orfane eliminate: {total_deleted}'))
            if reset_parent:
                self.stdout.write(self.style.SUCCESS(f'✓ Gruppi resettati per rigenerazione: {total_reset}'))

        self.stdout.write(self.style.SUCCESS('\nOperazione completata!'))
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.reports.models import SpendingPlan, PlannedExpense
from dateutil.relativedelta import relativedelta
import uuid
from decimal import Decimal


class Command(BaseCommand):
    help = 'Genera piani futuri per spese ricorrenti pianificate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe creato senza salvare',
        )
        parser.add_argument(
            '--months-ahead',
            type=int,
            default=12,
            help='Numero di mesi futuri da generare (default: 12)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        months_ahead = options['months_ahead']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODALITÀ DRY-RUN: Nessuna modifica verrà salvata')
            )

        # Trova tutte le spese pianificate ricorrenti
        recurring_expenses = PlannedExpense.objects.filter(
            is_recurring=True,
            total_installments__gt=1
        )

        self.stdout.write(f"Trovate {recurring_expenses.count()} spese ricorrenti")

        for expense in recurring_expenses:
            self.process_recurring_expense(expense, months_ahead, dry_run)

    def process_recurring_expense(self, expense, months_ahead, dry_run):
        """Processa una singola spesa ricorrente"""

        # Se non ha parent_recurring_id, è la prima rata - genera ID
        if not expense.parent_recurring_id:
            expense.parent_recurring_id = str(uuid.uuid4())
            if not dry_run:
                expense.save(update_fields=['parent_recurring_id'])

        # Calcola le rate mancanti
        existing_installments = PlannedExpense.objects.filter(
            parent_recurring_id=expense.parent_recurring_id
        ).count()

        missing_installments = expense.total_installments - existing_installments

        if missing_installments <= 0:
            self.stdout.write(f"✓ {expense.description}: tutte le rate già generate")
            return

        self.stdout.write(
            f"→ {expense.description}: generate {existing_installments}/"
            f"{expense.total_installments}, mancanti: {missing_installments}"
        )

        # Genera rate mancanti
        current_plan = expense.spending_plan
        current_date = current_plan.start_date

        for i in range(existing_installments + 1, expense.total_installments + 1):
            # Calcola la data per questa rata
            if expense.recurring_frequency == 'monthly':
                installment_date = current_date + relativedelta(months=i-1)
            elif expense.recurring_frequency == 'bimonthly':
                installment_date = current_date + relativedelta(months=(i-1)*2)
            elif expense.recurring_frequency == 'quarterly':
                installment_date = current_date + relativedelta(months=(i-1)*3)
            else:
                installment_date = current_date + relativedelta(months=i-1)

            # Trova o crea il piano per questo mese
            plan = self.get_or_create_plan_for_date(
                installment_date, current_plan, dry_run
            )

            if plan:
                # Crea la rata
                self.create_installment(
                    expense, plan, i, installment_date, dry_run
                )

    def get_or_create_plan_for_date(self, target_date, template_plan, dry_run):
        """Trova o crea un piano per la data target"""

        # Cerca piano esistente per questo mese
        existing_plan = SpendingPlan.objects.filter(
            plan_type='monthly',
            start_date__year=target_date.year,
            start_date__month=target_date.month
        ).first()

        if existing_plan:
            return existing_plan

        # Crea nuovo piano
        start_date = target_date.replace(day=1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)

        plan_name = f"{target_date.strftime('%B %Y').title()}"

        self.stdout.write(f"  → Creando piano: {plan_name}")

        if dry_run:
            return None

        new_plan = SpendingPlan.objects.create(
            name=plan_name,
            description=f"Piano auto-generato per {plan_name}",
            plan_type='monthly',
            start_date=start_date,
            end_date=end_date,
            total_budget=template_plan.total_budget,
            is_shared=template_plan.is_shared,
            created_by=template_plan.created_by,
            auto_generated=True,
            is_hidden=True  # Nascosto per default
        )

        # Copia gli utenti
        new_plan.users.set(template_plan.users.all())

        return new_plan

    def create_installment(self, original_expense, target_plan, installment_number, due_date, dry_run):
        """Crea una nuova rata nel piano target"""

        installment_description = (
            f"{original_expense.description} "
            f"(rata {installment_number}/{original_expense.total_installments})"
        )

        self.stdout.write(f"    → {installment_description} in {target_plan.name}")

        if dry_run:
            return

        PlannedExpense.objects.create(
            spending_plan=target_plan,
            description=installment_description,
            amount=original_expense.amount,
            category=original_expense.category,
            subcategory=original_expense.subcategory,
            priority=original_expense.priority,
            due_date=due_date,
            notes=f"Rata {installment_number} di {original_expense.total_installments} - Auto-generata",
            is_recurring=True,
            total_installments=original_expense.total_installments,
            installment_number=installment_number,
            parent_recurring_id=original_expense.parent_recurring_id,
            recurring_frequency=original_expense.recurring_frequency
        )
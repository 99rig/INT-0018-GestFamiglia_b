from django.core.management.base import BaseCommand
from apps.reports.models import PlannedExpense


class Command(BaseCommand):
    help = 'Sincronizza is_completed basandosi sui pagamenti effettivi'

    def handle(self, *args, **options):
        updated_count = 0
        unchanged_count = 0

        planned_expenses = PlannedExpense.objects.all()

        self.stdout.write(f"Controllo {planned_expenses.count()} spese pianificate...")

        for expense in planned_expenses:
            is_fully_paid = expense.is_fully_paid()

            if is_fully_paid and not expense.is_completed:
                expense.is_completed = True
                expense.save(update_fields=['is_completed'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Aggiornata: {expense.description} (Piano: {expense.spending_plan.name})"
                    )
                )
            elif not is_fully_paid and expense.is_completed:
                expense.is_completed = False
                expense.save(update_fields=['is_completed'])
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ Rimossa: {expense.description} (Piano: {expense.spending_plan.name})"
                    )
                )
            else:
                unchanged_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✨ Sincronizzazione completata: {updated_count} aggiornate, {unchanged_count} invariate"
            )
        )
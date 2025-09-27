from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Expense
from decimal import Decimal


@receiver(post_save, sender=Expense)
def update_planned_expense_completion(sender, instance, created, **kwargs):
    """
    Aggiorna automaticamente is_completed quando una spesa viene pagata
    Gestisce pagamenti completi e parziali
    """
    if instance.planned_expense:
        planned = instance.planned_expense

        # Calcola lo stato attuale
        total_paid = planned.get_total_paid()
        remaining = planned.get_remaining_amount()
        percentage = planned.get_completion_percentage()

        # Log dettagliato per debug
        print(f"📊 Aggiornamento '{planned.description}':")
        print(f"   - Importo totale: €{planned.amount}")
        print(f"   - Importo pagato: €{total_paid}")
        print(f"   - Rimanente: €{remaining}")
        print(f"   - Percentuale: {percentage:.1f}%")

        # Controlla se la spesa pianificata è completamente pagata
        if planned.is_fully_paid():
            if not planned.is_completed:
                planned.is_completed = True
                planned.save(update_fields=['is_completed'])
                print(f"✅ Spesa pianificata '{planned.description}' COMPLETATA (100%)")
        elif planned.is_partially_paid():
            # Pagamento parziale - mantieni is_completed = False ma mostra progresso
            if planned.is_completed:
                planned.is_completed = False
                planned.save(update_fields=['is_completed'])
            print(f"⚠️ Spesa pianificata '{planned.description}' PARZIALE ({percentage:.1f}%)")
        else:
            # Nessun pagamento
            if planned.is_completed:
                planned.is_completed = False
                planned.save(update_fields=['is_completed'])
                print(f"❌ Spesa pianificata '{planned.description}' NON PAGATA (0%)")


@receiver(post_delete, sender=Expense)
def update_planned_expense_on_delete(sender, instance, **kwargs):
    """
    Aggiorna is_completed quando una spesa viene eliminata
    """
    if instance.planned_expense:
        planned = instance.planned_expense

        # Ricontrolla lo stato dopo l'eliminazione
        if not planned.is_fully_paid() and planned.is_completed:
            planned.is_completed = False
            planned.save(update_fields=['is_completed'])
            print(f"⚠️ Spesa pianificata '{planned.description}' marcata come incompleta dopo eliminazione")
#!/usr/bin/env python
"""
Script per resettare tutti i dati di spese e piani di spesa
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.expenses.models import Expense, ExpenseQuota
from apps.reports.models import SpendingPlan, PlannedExpense

def reset_all_data():
    print('🗑️ Eliminando tutti i dati...')

    try:
        # Conta i dati prima della cancellazione
        try:
            quote_count = ExpenseQuota.objects.count()
        except:
            quote_count = 0
            print('⚠️  Tabella ExpenseQuota non trovata, ignoro')

        try:
            expense_count = Expense.objects.count()
        except:
            expense_count = 0
            print('⚠️  Tabella Expense non trovata, ignoro')

        try:
            planned_expense_count = PlannedExpense.objects.count()
        except:
            planned_expense_count = 0
            print('⚠️  Tabella PlannedExpense non trovata, ignoro')

        try:
            spending_plan_count = SpendingPlan.objects.count()
        except:
            spending_plan_count = 0
            print('⚠️  Tabella SpendingPlan non trovata, ignoro')

        print(f'📊 Dati da eliminare:')
        print(f'   - Quote: {quote_count}')
        print(f'   - Spese: {expense_count}')
        print(f'   - Spese pianificate: {planned_expense_count}')
        print(f'   - Piani di spesa: {spending_plan_count}')
        print()

        # Elimina tutti i dati nell'ordine corretto (rispettando le foreign key)
        print('🗑️ Eliminazione in corso...')

        # 1. Quote (dipendono dalle spese)
        try:
            deleted_count = ExpenseQuota.objects.all().delete()[0]
            print(f'✅ Quote eliminate: {deleted_count}')
        except Exception as e:
            print(f'⚠️  Errore eliminazione quote: {e}')

        # 2. Spese (possono dipendere dalle spese pianificate)
        try:
            deleted_count = Expense.objects.all().delete()[0]
            print(f'✅ Spese eliminate: {deleted_count}')
        except Exception as e:
            print(f'⚠️  Errore eliminazione spese: {e}')

        # 3. Spese pianificate (dipendono dai piani)
        try:
            deleted_count = PlannedExpense.objects.all().delete()[0]
            print(f'✅ Spese pianificate eliminate: {deleted_count}')
        except Exception as e:
            print(f'⚠️  Errore eliminazione spese pianificate: {e}')

        # 4. Piani di spesa
        try:
            deleted_count = SpendingPlan.objects.all().delete()[0]
            print(f'✅ Piani di spesa eliminati: {deleted_count}')
        except Exception as e:
            print(f'⚠️  Errore eliminazione piani: {e}')

        print()
        print('🎉 Reset completato! Situazione completamente pulita.')
        print('💡 Ora puoi creare nuovi piani di spesa e spese da zero.')

    except Exception as e:
        print(f'❌ Errore generale durante il reset: {e}')
        print('💡 Prova a eseguire le migrazioni prima: python manage.py migrate')

if __name__ == '__main__':
    reset_all_data()
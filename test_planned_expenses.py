#!/usr/bin/env python
"""
Test script for planned expenses workflow
Run this with: python test_planned_expenses.py
"""

import os
import sys
import django
from django.conf import settings

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.reports.models import SpendingPlan, PlannedExpense
from apps.expenses.models import Expense
from apps.categories.models import Category
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

def test_planned_expense_workflow():
    print("🧪 Testing Planned Expense Workflow")
    print("=" * 50)

    # 1. Get or create a test user
    try:
        user = User.objects.get(email='marco@test.com')
        print(f"✅ Using existing user: {user.email}")
    except User.DoesNotExist:
        print("❌ Test user not found. Please create a user first with email 'marco@test.com'")
        return False

    # 2. Create a test spending plan
    spending_plan = SpendingPlan.objects.create(
        name="Test Plan Ottobre 2025",
        description="Piano di test per spese pianificate",
        plan_type="monthly",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        is_active=True
    )
    spending_plan.users.add(user)
    print(f"✅ Created spending plan: {spending_plan.name}")

    # 3. Get or create a test category
    category, created = Category.objects.get_or_create(
        name="Test Category",
        defaults={
            'description': 'Categoria di test',
            'icon': 'test',
            'color': '#FF0000',
            'category_type': 'necessarie',
            'monthly_budget': Decimal('500.00')
        }
    )
    print(f"✅ Using category: {category.name}")

    # 4. Create a planned expense
    planned_expense = PlannedExpense.objects.create(
        spending_plan=spending_plan,
        description="Retta Thomas Test",
        amount=Decimal('400.00'),
        category=category,
        priority='high',
        due_date=date.today() + timedelta(days=15),
        notes="Test della spesa pianificata",
        is_completed=False
    )
    print(f"✅ Created planned expense: {planned_expense.description} - €{planned_expense.amount}")

    # 5. Test initial state
    print(f"\n📊 Initial State:")
    print(f"   Total planned: €{planned_expense.amount}")
    print(f"   Total paid: €{planned_expense.get_total_paid()}")
    print(f"   Remaining: €{planned_expense.get_remaining_amount()}")
    print(f"   Payment status: {planned_expense.get_payment_status()}")
    print(f"   Completion %: {planned_expense.get_completion_percentage():.1f}%")

    # 6. Add first payment (partial)
    expense1 = Expense.objects.create(
        user=user,
        description="Pagamento Marco per Retta Thomas",
        amount=Decimal('300.00'),
        category=category,
        date=date.today(),
        status='pagata',
        planned_expense=planned_expense
    )
    print(f"\n💰 Added first payment: €{expense1.amount} by {expense1.user.first_name or expense1.user.email}")

    # Refresh and check state
    planned_expense.refresh_from_db()
    print(f"📊 After first payment:")
    print(f"   Total paid: €{planned_expense.get_total_paid()}")
    print(f"   Remaining: €{planned_expense.get_remaining_amount()}")
    print(f"   Payment status: {planned_expense.get_payment_status()}")
    print(f"   Completion %: {planned_expense.get_completion_percentage():.1f}%")
    print(f"   Is partially paid: {planned_expense.is_partially_paid()}")
    print(f"   Is fully paid: {planned_expense.is_fully_paid()}")

    # 7. Add second payment (complete the planned expense)
    expense2 = Expense.objects.create(
        user=user,
        description="Pagamento Sara per Retta Thomas",
        amount=Decimal('100.00'),
        category=category,
        date=date.today(),
        status='pagata',
        planned_expense=planned_expense
    )
    print(f"\n💰 Added second payment: €{expense2.amount} by Sara (simulated)")

    # Final state
    planned_expense.refresh_from_db()
    print(f"📊 Final state:")
    print(f"   Total paid: €{planned_expense.get_total_paid()}")
    print(f"   Remaining: €{planned_expense.get_remaining_amount()}")
    print(f"   Payment status: {planned_expense.get_payment_status()}")
    print(f"   Completion %: {planned_expense.get_completion_percentage():.1f}%")
    print(f"   Is partially paid: {planned_expense.is_partially_paid()}")
    print(f"   Is fully paid: {planned_expense.is_fully_paid()}")

    # 8. Test related expenses query
    related_expenses = planned_expense.get_related_expenses()
    print(f"\n🔗 Related expenses ({related_expenses.count()}):")
    for exp in related_expenses:
        print(f"   - {exp.description}: €{exp.amount} ({exp.date})")

    # 9. Test the API model methods work correctly
    assert planned_expense.get_total_paid() == Decimal('400.00'), "Total paid should be 400.00"
    assert planned_expense.get_remaining_amount() == Decimal('0.00'), "Remaining should be 0.00"
    assert planned_expense.is_fully_paid() == True, "Should be fully paid"
    assert planned_expense.get_payment_status() == 'completed', "Status should be completed"
    assert planned_expense.get_completion_percentage() == 100.0, "Completion should be 100%"

    print(f"\n✅ All tests passed! Planned expense workflow is working correctly.")

    # Cleanup (optional)
    print(f"\n🧹 Cleaning up test data...")
    expense1.delete()
    expense2.delete()
    planned_expense.delete()
    spending_plan.delete()
    if created:
        category.delete()
    print(f"✅ Cleanup completed.")

    return True

if __name__ == "__main__":
    try:
        success = test_planned_expense_workflow()
        if success:
            print(f"\n🎉 Test completed successfully!")
        else:
            print(f"\n❌ Test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
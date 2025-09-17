from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseViewSet, RecurringExpenseViewSet, ExpenseQuotaViewSet, BudgetViewSet

router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'recurring-expenses', RecurringExpenseViewSet, basename='recurring-expense')
router.register(r'quote', ExpenseQuotaViewSet, basename='expense-quota')
router.register(r'budgets', BudgetViewSet, basename='budget')

urlpatterns = [
    path('', include(router.urls)),
]
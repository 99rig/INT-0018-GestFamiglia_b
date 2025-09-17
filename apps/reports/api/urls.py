from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BudgetViewSet, SavingGoalViewSet, PlannedExpenseViewSet

router = DefaultRouter()
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'saving-goals', SavingGoalViewSet, basename='saving-goal')
router.register(r'planned-expenses', PlannedExpenseViewSet, basename='planned-expense')

urlpatterns = [
    path('', include(router.urls)),
]
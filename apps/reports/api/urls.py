from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BudgetViewSet, SavingGoalViewSet

router = DefaultRouter()
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'saving-goals', SavingGoalViewSet, basename='saving-goal')

urlpatterns = [
    path('', include(router.urls)),
]
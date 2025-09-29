from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContributionViewSet, ExpenseContributionViewSet

app_name = 'contributions'

router = DefaultRouter()
router.register(r'contributions', ContributionViewSet, basename='contribution')
router.register(r'expense-contributions', ExpenseContributionViewSet, basename='expense-contribution')

urlpatterns = [
    path('', include(router.urls)),
]
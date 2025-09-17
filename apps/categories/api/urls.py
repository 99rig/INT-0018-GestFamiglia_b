from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, SubcategoryViewSet, get_subcategories_by_category

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/subcategories-by-category/', get_subcategories_by_category, name='admin_subcategories_by_category'),
]
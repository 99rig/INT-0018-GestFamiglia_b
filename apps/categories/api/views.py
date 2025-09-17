from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from apps.categories.models import Category, Subcategory
from .serializers import (
    CategorySerializer,
    CategoryCreateUpdateSerializer,
    SubcategorySerializer,
    SubcategoryCreateUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle categorie"""
    queryset = Category.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['type', 'name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategorySerializer
    
    @action(detail=False, methods=['get'])
    def necessarie(self, request):
        """Restituisce solo le categorie necessarie"""
        categories = self.queryset.filter(type='necessaria')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def extra(self, request):
        """Restituisce solo le categorie extra"""
        categories = self.queryset.filter(type='extra')
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Restituisce le sottocategorie di una categoria"""
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = SubcategorySerializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Restituisce statistiche per la categoria"""
        from django.db.models import Sum, Count, Avg
        from datetime import datetime, timedelta
        
        category = self.get_object()
        today = datetime.today()
        
        # Statistiche del mese corrente
        current_month_stats = category.expenses.filter(
            date__year=today.year,
            date__month=today.month,
            status='pagata'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id'),
            average=Avg('amount')
        )
        
        # Statistiche degli ultimi 30 giorni
        thirty_days_ago = today - timedelta(days=30)
        last_30_days_stats = category.expenses.filter(
            date__gte=thirty_days_ago,
            status='pagata'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id'),
            average=Avg('amount')
        )
        
        return Response({
            'category': CategorySerializer(category).data,
            'current_month': {
                'total': str(current_month_stats['total'] or 0),
                'count': current_month_stats['count'],
                'average': str(current_month_stats['average'] or 0)
            },
            'last_30_days': {
                'total': str(last_30_days_stats['total'] or 0),
                'count': last_30_days_stats['count'],
                'average': str(last_30_days_stats['average'] or 0)
            },
            'budget_status': {
                'monthly_budget': str(category.monthly_budget or 0),
                'spent': str(current_month_stats['total'] or 0),
                'remaining': str((category.monthly_budget or 0) - (current_month_stats['total'] or 0))
            }
        })


class SubcategoryViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle sottocategorie"""
    queryset = Subcategory.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['category', 'name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SubcategoryCreateUpdateSerializer
        return SubcategorySerializer


@staff_member_required
@require_GET
def get_subcategories_by_category(request):
    """
    Vista per ottenere le sottocategorie filtrate per categoria
    Usata per le select dinamiche nell'admin
    """
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'subcategories': []})
    
    try:
        subcategories = Subcategory.objects.filter(
            category_id=category_id,
            is_active=True
        ).values('id', 'name').order_by('name')
        
        return JsonResponse({
            'subcategories': list(subcategories)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
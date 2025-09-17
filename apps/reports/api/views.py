from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime
from apps.reports.models import Budget, BudgetCategory, SavingGoal
from apps.expenses.models import Expense
from .serializers import (
    BudgetSerializer,
    BudgetCreateUpdateSerializer,
    BudgetCategorySerializer,
    BudgetCategoryCreateUpdateSerializer,
    SavingGoalSerializer,
    SavingGoalCreateUpdateSerializer
)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione dei budget"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['year', 'month', 'is_active']
    ordering_fields = ['year', 'month', 'total_amount']
    ordering = ['-year', '-month']
    
    def get_queryset(self):
        """Restituisce i budget a cui l'utente appartiene"""
        return Budget.objects.filter(users=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BudgetCreateUpdateSerializer
        return BudgetSerializer
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Restituisce il budget del mese corrente"""
        today = datetime.today()
        budget = Budget.objects.filter(
            users=request.user,
            year=today.year,
            month=today.month,
            is_active=True
        ).first()
        
        if budget:
            serializer = BudgetSerializer(budget)
            return Response(serializer.data)
        return Response(
            {'detail': 'Nessun budget trovato per il mese corrente.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def add_category(self, request, pk=None):
        """Aggiunge una categoria al budget"""
        budget = self.get_object()
        serializer = BudgetCategoryCreateUpdateSerializer(data={
            'budget': budget.id,
            'category': request.data.get('category'),
            'amount': request.data.get('amount')
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def copy_to_next_month(self, request, pk=None):
        """Copia il budget al mese successivo"""
        budget = self.get_object()
        
        # Calcola il mese successivo
        next_month = budget.month + 1
        next_year = budget.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # Verifica se esiste già un budget
        if Budget.objects.filter(
            name=budget.name,
            year=next_year,
            month=next_month
        ).exists():
            return Response(
                {'detail': 'Esiste già un budget per il periodo selezionato.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crea il nuovo budget
        new_budget = Budget.objects.create(
            name=budget.name,
            description=f"Copiato da {budget.month}/{budget.year}",
            year=next_year,
            month=next_month,
            total_amount=budget.total_amount,
            is_active=True
        )
        new_budget.users.set(budget.users.all())
        
        # Copia le categorie
        for cat_budget in budget.category_budgets.all():
            BudgetCategory.objects.create(
                budget=new_budget,
                category=cat_budget.category,
                amount=cat_budget.amount
            )
        
        serializer = BudgetSerializer(new_budget)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """Confronto tra budget di diversi mesi"""
        months = int(request.query_params.get('months', 6))
        today = datetime.today()
        
        comparison_data = []
        for i in range(months):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            
            budget = Budget.objects.filter(
                users=request.user,
                year=year,
                month=month
            ).first()
            
            if budget:
                spent = budget.get_spent_amount()
                comparison_data.append({
                    'year': year,
                    'month': month,
                    'budget_name': budget.name,
                    'budget_amount': str(budget.total_amount),
                    'spent_amount': str(spent),
                    'remaining': str(budget.total_amount - spent),
                    'percentage': float(budget.get_percentage_used())
                })
            else:
                # Se non c'� budget, mostra solo le spese
                spent = Expense.objects.filter(
                    user=request.user,
                    date__year=year,
                    date__month=month,
                    status='pagata'
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                comparison_data.append({
                    'year': year,
                    'month': month,
                    'budget_name': None,
                    'budget_amount': '0',
                    'spent_amount': str(spent),
                    'remaining': '0',
                    'percentage': 0
                })
        
        return Response(comparison_data)


class SavingGoalViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione degli obiettivi di risparmio"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_completed']
    ordering_fields = ['target_amount', 'target_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Restituisce gli obiettivi a cui l'utente appartiene"""
        return SavingGoal.objects.filter(users=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SavingGoalCreateUpdateSerializer
        return SavingGoalSerializer
    
    @action(detail=True, methods=['post'])
    def add_amount(self, request, pk=None):
        """Aggiunge un importo all'obiettivo di risparmio"""
        goal = self.get_object()
        amount = request.data.get('amount', 0)
        
        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {'detail': 'L\'importo deve essere positivo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Importo non valido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.current_amount += amount
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
        goal.save()
        
        serializer = SavingGoalSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def withdraw_amount(self, request, pk=None):
        """Preleva un importo dall'obiettivo di risparmio"""
        goal = self.get_object()
        amount = request.data.get('amount', 0)
        
        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {'detail': 'L\'importo deve essere positivo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if amount > goal.current_amount:
                return Response(
                    {'detail': 'Importo superiore al saldo disponibile.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Importo non valido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.current_amount -= amount
        goal.is_completed = False
        goal.save()
        
        serializer = SavingGoalSerializer(goal)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_goals(self, request):
        """Restituisce solo gli obiettivi attivi (non completati)"""
        goals = self.get_queryset().filter(is_completed=False)
        serializer = SavingGoalSerializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed_goals(self, request):
        """Restituisce solo gli obiettivi completati"""
        goals = self.get_queryset().filter(is_completed=True)
        serializer = SavingGoalSerializer(goals, many=True)
        return Response(serializer.data)
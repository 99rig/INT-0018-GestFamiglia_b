from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime
from apps.reports.models import Budget, BudgetCategory, SavingGoal, PlannedExpense
from apps.expenses.models import Expense
from .serializers import (
    BudgetSerializer,
    BudgetCreateUpdateSerializer,
    BudgetCategorySerializer,
    BudgetCategoryCreateUpdateSerializer,
    SavingGoalSerializer,
    SavingGoalCreateUpdateSerializer,
    PlannedExpenseSerializer,
    PlannedExpenseCreateUpdateSerializer
)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione dei budget"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['plan_type', 'is_active']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date', '-created_at']
    
    def get_queryset(self):
        """Restituisce i budget della famiglia dell'utente"""
        user = self.request.user

        # Se l'utente non appartiene a nessuna famiglia, non vede nessun budget
        if not user.family:
            return Budget.objects.none()

        # Filtra per budget che includono utenti della stessa famiglia
        family_users = user.family.members.all()
        return Budget.objects.filter(users__in=family_users).distinct()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BudgetCreateUpdateSerializer
        return BudgetSerializer
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Restituisce i budget attivi nel periodo corrente della famiglia"""
        from django.utils import timezone
        today = timezone.now().date()
        user = request.user

        # Se l'utente non appartiene a nessuna famiglia, non vede nessun budget
        if not user.family:
            return Response([])

        # Filtra per budget attivi che includono utenti della stessa famiglia
        family_users = user.family.members.all()
        budgets = Budget.objects.filter(
            users__in=family_users,
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        ).distinct()

        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data)
    
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
    def copy_to_next_period(self, request, pk=None):
        """Copia il budget al periodo successivo"""
        budget = self.get_object()
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        # Calcola il periodo successivo
        period_length = (budget.end_date - budget.start_date).days
        new_start_date = budget.end_date + timedelta(days=1)
        new_end_date = new_start_date + timedelta(days=period_length)

        # Verifica se esiste già un budget sovrapposto
        if Budget.objects.filter(
            name=budget.name,
            start_date__lte=new_end_date,
            end_date__gte=new_start_date
        ).exists():
            return Response(
                {'detail': 'Esiste già un budget per il periodo selezionato.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crea il nuovo budget
        new_budget = Budget.objects.create(
            name=budget.name,
            description=f"Copiato da {budget.start_date} - {budget.end_date}",
            plan_type=budget.plan_type,
            start_date=new_start_date,
            end_date=new_end_date,
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


class PlannedExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle spese pianificate"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'priority', 'is_completed', 'spending_plan']
    ordering_fields = ['due_date', 'amount', 'priority', 'created_at']
    ordering = ['due_date', '-priority', 'created_at']

    def get_queryset(self):
        """Restituisce le spese pianificate della famiglia dell'utente"""
        user = self.request.user

        # Se l'utente non appartiene a nessuna famiglia, non vede nessuna spesa pianificata
        if not user.family:
            return PlannedExpense.objects.none()

        # Filtra per spese pianificate che appartengono a spending plan della famiglia
        family_users = user.family.members.all()
        return PlannedExpense.objects.filter(
            spending_plan__users__in=family_users
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PlannedExpenseCreateUpdateSerializer
        return PlannedExpenseSerializer

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Aggiunge un pagamento a una spesa pianificata"""
        planned_expense = self.get_object()

        # Validazione dei dati del pagamento
        amount = request.data.get('amount')
        description = request.data.get('description', f'Pagamento per {planned_expense.description}')
        category = request.data.get('category', planned_expense.category)
        subcategory = request.data.get('subcategory', planned_expense.subcategory)
        date = request.data.get('date')

        if not amount:
            return Response(
                {'detail': 'Importo del pagamento obbligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'detail': 'L\'importo deve essere maggiore di zero.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Importo non valido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica che il pagamento non superi l'importo rimanente
        remaining = planned_expense.get_remaining_amount()
        if amount > remaining:
            return Response(
                {'detail': f'Il pagamento di €{amount} supera l\'importo rimanente di €{remaining}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crea la spesa reale collegata
        expense_data = {
            'description': description,
            'amount': amount,
            'category': category.id if category else None,
            'subcategory': subcategory.id if subcategory else None,
            'user': request.user,
            'date': date or datetime.now().date(),
            'status': 'pagata',
            'planned_expense': planned_expense
        }

        from apps.expenses.models import Expense
        expense = Expense.objects.create(**expense_data)

        # Aggiorna lo stato della spesa pianificata se completamente pagata
        if planned_expense.is_fully_paid():
            planned_expense.is_completed = True
            planned_expense.save()

        serializer = PlannedExpenseSerializer(planned_expense)
        return Response({
            'planned_expense': serializer.data,
            'expense_id': expense.id,
            'message': 'Pagamento aggiunto con successo.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Filtra le spese pianificate per stato di pagamento"""
        status_filter = request.query_params.get('status', 'all')
        queryset = self.get_queryset()

        if status_filter == 'pending':
            # Spese non ancora pagate
            queryset = [pe for pe in queryset if pe.get_payment_status() == 'pending']
        elif status_filter == 'partial':
            # Spese parzialmente pagate
            queryset = [pe for pe in queryset if pe.get_payment_status() == 'partial']
        elif status_filter == 'completed':
            # Spese completamente pagate
            queryset = [pe for pe in queryset if pe.get_payment_status() == 'completed']
        elif status_filter == 'overdue':
            # Spese scadute
            queryset = [pe for pe in queryset if pe.get_payment_status() == 'overdue']

        serializer = PlannedExpenseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Restituisce le spese pianificate in scadenza nei prossimi giorni"""
        from datetime import timedelta
        from django.utils import timezone

        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        due_date = today + timedelta(days=days)

        queryset = self.get_queryset().filter(
            due_date__lte=due_date,
            due_date__gte=today,
            is_completed=False
        )

        serializer = PlannedExpenseSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def payment_summary(self, request):
        """Riepilogo dei pagamenti per tutte le spese pianificate"""
        queryset = self.get_queryset()

        summary = {
            'total_planned': 0,
            'total_paid': 0,
            'total_remaining': 0,
            'completed_count': 0,
            'partial_count': 0,
            'pending_count': 0,
            'overdue_count': 0
        }

        for pe in queryset:
            summary['total_planned'] += float(pe.amount)
            summary['total_paid'] += float(pe.get_total_paid())
            summary['total_remaining'] += float(pe.get_remaining_amount())

            status = pe.get_payment_status()
            if status == 'completed':
                summary['completed_count'] += 1
            elif status == 'partial':
                summary['partial_count'] += 1
            elif status == 'pending':
                summary['pending_count'] += 1
            elif status == 'overdue':
                summary['overdue_count'] += 1

        return Response(summary)
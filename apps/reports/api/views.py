from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from apps.reports.models import Budget, BudgetCategory, SavingGoal, PlannedExpense, SpendingPlan
from apps.expenses.models import Expense
from .serializers import (
    BudgetSerializer,
    BudgetCreateUpdateSerializer,
    BudgetCategorySerializer,
    BudgetCategoryCreateUpdateSerializer,
    SavingGoalSerializer,
    SavingGoalCreateUpdateSerializer,
    PlannedExpenseSerializer,
    PlannedExpenseCreateUpdateSerializer,
    SpendingPlanSerializer,
    SpendingPlanCreateUpdateSerializer
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
        ).select_related(
            'spending_plan', 'category', 'subcategory'
        ).prefetch_related(
            'actual_expense'  # Per get_related_expenses()
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

        # Handle category - can be an ID from request or Category instance from planned_expense
        category_data = request.data.get('category')
        if category_data is not None:
            # If category comes from request, it's likely an ID, convert to Category instance
            from apps.categories.models import Category
            if isinstance(category_data, (int, str)):
                try:
                    category = Category.objects.get(id=int(category_data))
                except Category.DoesNotExist:
                    category = planned_expense.category
            else:
                category = category_data
        else:
            category = planned_expense.category

        # Handle subcategory - can be an ID from request or Subcategory instance from planned_expense
        subcategory_data = request.data.get('subcategory')
        if subcategory_data is not None:
            # If subcategory comes from request, it's likely an ID, convert to Subcategory instance
            from apps.categories.models import Subcategory
            if isinstance(subcategory_data, (int, str)):
                try:
                    subcategory = Subcategory.objects.get(id=int(subcategory_data))
                except Subcategory.DoesNotExist:
                    subcategory = planned_expense.subcategory
            else:
                subcategory = subcategory_data
        else:
            subcategory = planned_expense.subcategory

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
            'category': category,
            'subcategory': subcategory,
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


class SpendingPlanViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione dei piani di spesa"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['plan_type', 'is_active']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date', '-created_at']

    def get_queryset(self):
        """Restituisce i piani di spesa visibili all'utente (personali + famiglia)"""
        user = self.request.user
        from django.db.models import Q

        # Piani personali (creati dall'utente e non condivisi)
        personal_plans = Q(created_by=user, is_shared=False)

        # Piani condivisi con la famiglia (se l'utente ha una famiglia)
        family_plans = Q()
        if user.family:
            family_users = user.family.members.all()
            family_plans = Q(users__in=family_users, is_shared=True)

        # Restituisci piani personali + piani famiglia con ottimizzazioni
        return SpendingPlan.objects.filter(
            personal_plans | family_plans
        ).select_related(
            'created_by'
        ).prefetch_related(
            'users',
            'planned_expenses__category',
            'planned_expenses__subcategory'
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SpendingPlanCreateUpdateSerializer
        return SpendingPlanSerializer

    def perform_create(self, serializer):
        """Salva automaticamente il creatore del piano"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Restituisce i piani di spesa attivi nel periodo corrente della famiglia"""
        from django.utils import timezone
        today = timezone.now().date()
        user = request.user

        # Se l'utente non appartiene a nessuna famiglia, non vede nessun piano
        if not user.family:
            return Response([])

        # Filtra per piani attivi che includono utenti della stessa famiglia
        family_users = user.family.members.all()
        plans = SpendingPlan.objects.filter(
            users__in=family_users,
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        ).distinct()

        serializer = SpendingPlanSerializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def copy_to_next_period(self, request, pk=None):
        """Copia il piano di spesa al periodo successivo"""
        plan = self.get_object()
        from datetime import timedelta

        # Calcola il periodo successivo
        period_length = (plan.end_date - plan.start_date).days
        new_start_date = plan.end_date + timedelta(days=1)
        new_end_date = new_start_date + timedelta(days=period_length)

        # Verifica se esiste già un piano sovrapposto
        if SpendingPlan.objects.filter(
            name=plan.name,
            start_date__lte=new_end_date,
            end_date__gte=new_start_date
        ).exists():
            return Response(
                {'detail': 'Esiste già un piano per il periodo selezionato.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crea il nuovo piano
        new_plan = SpendingPlan.objects.create(
            name=plan.name,
            description=f"Copiato da {plan.start_date} - {plan.end_date}",
            plan_type=plan.plan_type,
            start_date=new_start_date,
            end_date=new_end_date,
            is_active=True
        )
        new_plan.users.set(plan.users.all())

        # Copia le spese pianificate
        for planned_expense in plan.planned_expenses.all():
            PlannedExpense.objects.create(
                spending_plan=new_plan,
                description=planned_expense.description,
                amount=planned_expense.amount,
                category=planned_expense.category,
                subcategory=planned_expense.subcategory,
                priority=planned_expense.priority,
                notes=planned_expense.notes
            )

        serializer = SpendingPlanSerializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def smart_clone(self, request, pk=None):
        """Clona intelligentemente un piano di spesa con riconoscimento pattern e date"""
        plan = self.get_object()
        from apps.reports.utils.plan_pattern_recognition import generate_intelligent_clone_data

        # Controlla se è solo preview o creazione effettiva
        preview_only = request.data.get('preview_only', False)

        # Usa il nuovo utility per generare i dati del clone
        clone_data = generate_intelligent_clone_data(
            plan_name=plan.name,
            start_date=plan.start_date,
            end_date=plan.end_date,
            plan_type=plan.plan_type
        )

        new_title = clone_data['new_title']
        new_start_date = clone_data['new_start_date']
        new_end_date = clone_data['new_end_date']
        pattern_detection = clone_data['pattern_detection']

        # Verifica se esiste già un piano sovrapposto
        existing_plan = SpendingPlan.objects.filter(
            name=new_title,
            start_date__lte=new_end_date,
            end_date__gte=new_start_date
        ).first()

        if existing_plan:
            return Response({
                'detail': f'Esiste già un piano "{new_title}" per il periodo selezionato.',
                'suggested_title': new_title,
                'suggested_start_date': new_start_date.isoformat(),
                'suggested_end_date': new_end_date.isoformat(),
                'conflict_with_existing_plan': {
                    'id': existing_plan.id,
                    'name': existing_plan.name,
                    'period': f"{existing_plan.start_date} - {existing_plan.end_date}"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Se è solo preview, restituisci i dati senza creare nulla
        if preview_only:
            # Simula le spese clonate senza salvarle
            simulated_expenses = []
            for planned_expense in plan.planned_expenses.all():
                # Calcola la nuova data di scadenza
                if planned_expense.due_date:
                    days_from_start = (planned_expense.due_date - plan.start_date).days
                    new_due_date = new_start_date + timedelta(days=days_from_start)
                    if new_due_date > new_end_date:
                        new_due_date = new_end_date
                else:
                    new_due_date = None

                simulated_expenses.append({
                    'id': None,  # Non esiste ancora
                    'description': planned_expense.description,
                    'amount': str(planned_expense.amount),
                    'category': planned_expense.category.id if planned_expense.category else None,
                    'category_name': planned_expense.category.name if planned_expense.category else None,
                    'subcategory': planned_expense.subcategory.id if planned_expense.subcategory else None,
                    'priority': planned_expense.priority,
                    'due_date': new_due_date.isoformat() if new_due_date else None,
                    'notes': planned_expense.notes
                })

            # Prepara risposta preview
            preview_data = {
                'cloned_plan': {
                    'id': None,  # Non esiste ancora
                    'name': new_title,
                    'description': plan.description,
                    'plan_type': plan.plan_type,
                    'total_budget': str(plan.total_budget) if plan.total_budget else None,
                    'start_date': new_start_date.isoformat(),
                    'end_date': new_end_date.isoformat(),
                    'is_shared': plan.is_shared,
                    'planned_expenses_detail': simulated_expenses
                },
                'cloning_details': {
                    'original_plan': {
                        'id': plan.id,
                        'name': plan.name,
                        'period': f"{plan.start_date} - {plan.end_date}"
                    },
                    'pattern_detection': pattern_detection,
                    'new_period': {
                        'start_date': new_start_date.isoformat(),
                        'end_date': new_end_date.isoformat(),
                        'title': new_title
                    },
                    'expenses_cloned': len(simulated_expenses),
                    'expenses_with_dates_adjusted': len([e for e in simulated_expenses if e['due_date']])
                }
            }

            return Response(preview_data, status=status.HTTP_200_OK)

        # Se non è preview, crea effettivamente il piano
        new_plan = SpendingPlan.objects.create(
            name=new_title,
            description=plan.description,
            plan_type=plan.plan_type,
            total_budget=plan.total_budget,
            start_date=new_start_date,
            end_date=new_end_date,
            is_shared=plan.is_shared,
            is_active=True,
            created_by=request.user
        )

        # Copia gli utenti
        new_plan.users.set(plan.users.all())

        # Clona le spese pianificate
        cloned_expenses = []
        for planned_expense in plan.planned_expenses.all():
            if planned_expense.due_date:
                days_from_start = (planned_expense.due_date - plan.start_date).days
                new_due_date = new_start_date + timedelta(days=days_from_start)
                if new_due_date > new_end_date:
                    new_due_date = new_end_date
            else:
                new_due_date = None

            cloned_expense = PlannedExpense.objects.create(
                spending_plan=new_plan,
                description=planned_expense.description,
                amount=planned_expense.amount,
                category=planned_expense.category,
                subcategory=planned_expense.subcategory,
                priority=planned_expense.priority,
                due_date=new_due_date,
                notes=planned_expense.notes
            )
            cloned_expenses.append(cloned_expense)

        # Prepara risposta con piano creato
        response_data = {
            'cloned_plan': SpendingPlanSerializer(new_plan).data,
            'cloning_details': {
                'original_plan': {
                    'id': plan.id,
                    'name': plan.name,
                    'period': f"{plan.start_date} - {plan.end_date}"
                },
                'pattern_detection': pattern_detection,
                'new_period': {
                    'start_date': new_start_date.isoformat(),
                    'end_date': new_end_date.isoformat(),
                    'title': new_title
                },
                'expenses_cloned': len(cloned_expenses),
                'expenses_with_dates_adjusted': len([e for e in cloned_expenses if e.due_date])
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Endpoint ottimizzato per ottenere piano + spese pianificate + spese reali in una sola chiamata"""
        plan = self.get_object()

        # Precarica tutto quello che serve con una query ottimizzata
        plan_data = SpendingPlan.objects.filter(
            pk=plan.pk
        ).select_related(
            'created_by'
        ).prefetch_related(
            'users',
            'planned_expenses__category',
            'planned_expenses__subcategory',
            # Precarica le spese reali collegate alle pianificate
            'planned_expenses__expense_set'
        ).first()

        # Serializza il piano con tutte le spese pianificate usando il serializer ottimizzato
        from .serializers import SpendingPlanDetailSerializer
        plan_serializer = SpendingPlanDetailSerializer(plan_data)

        # Carica le spese reali del piano (non collegate a spese pianificate)
        from apps.expenses.models import Expense
        unplanned_expenses = Expense.objects.filter(
            spending_plan=plan,
            planned_expense__isnull=True  # Solo spese NON collegate a pianificate
        ).select_related(
            'category', 'subcategory', 'user'
        )

        # Serializza le spese non pianificate
        from apps.expenses.api.serializers import ExpenseSerializer
        unplanned_serializer = ExpenseSerializer(unplanned_expenses, many=True)

        return Response({
            'plan': plan_serializer.data,
            'unplanned_expenses': unplanned_serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Statistiche generali sui piani di spesa della famiglia"""
        user = request.user

        if not user.family:
            return Response({
                'total_plans': 0,
                'active_plans': 0,
                'total_planned_amount': '0.00',
                'total_spent_amount': '0.00',
                'average_completion': 0.0
            })

        family_users = user.family.members.all()
        plans = SpendingPlan.objects.filter(users__in=family_users).distinct()

        total_plans = plans.count()
        active_plans = plans.filter(is_active=True).count()

        total_planned = sum(float(plan.get_total_planned_amount()) for plan in plans)
        total_spent = sum(float(plan.get_completed_expenses_amount()) for plan in plans)

        # Calcola la media di completamento
        completion_percentages = [float(plan.get_completion_percentage()) for plan in plans if plan.get_total_expenses_count() > 0]
        average_completion = sum(completion_percentages) / len(completion_percentages) if completion_percentages else 0.0

        return Response({
            'total_plans': total_plans,
            'active_plans': active_plans,
            'total_planned_amount': str(total_planned),
            'total_spent_amount': str(total_spent),
            'average_completion': round(average_completion, 2)
        })
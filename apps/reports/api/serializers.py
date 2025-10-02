from rest_framework import serializers
from apps.reports.models import Budget, BudgetCategory, SavingGoal, SpendingPlan, PlannedExpense
from apps.categories.api.serializers import CategorySerializer
from apps.users.api.serializers import UserSerializer


class BudgetCategorySerializer(serializers.ModelSerializer):
    """Serializer per le categorie di budget"""
    category_detail = CategorySerializer(source='category', read_only=True)
    spent_amount = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategory
        fields = [
            'id', 'category', 'category_detail', 'amount',
            'spent_amount', 'percentage_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'spent_amount', 'percentage_used']

    def get_spent_amount(self, obj):
        """Restituisce l'importo speso per questa categoria"""
        return str(obj.get_spent_amount())

    def get_percentage_used(self, obj):
        """Restituisce la percentuale utilizzata"""
        return float(obj.get_percentage_used())


class PlannedExpenseSerializer(serializers.ModelSerializer):
    """Serializer per le spese pianificate"""
    category_detail = CategorySerializer(source='category', read_only=True)
    subcategory_detail = CategorySerializer(source='subcategory', read_only=True)

    # Campi calcolati per il tracking dei pagamenti
    total_paid = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    is_partially_paid = serializers.SerializerMethodField()
    actual_payments_count = serializers.SerializerMethodField()
    paid_by_users = serializers.SerializerMethodField()
    my_share = serializers.SerializerMethodField()
    other_share = serializers.SerializerMethodField()

    class Meta:
        model = PlannedExpense
        fields = [
            'id', 'spending_plan', 'description', 'amount', 'category', 'category_detail',
            'subcategory', 'subcategory_detail', 'priority', 'due_date',
            'notes', 'is_completed', 'is_hidden', 'payment_type', 'my_share_amount', 'paid_by_user', 'created_at', 'updated_at',
            'total_paid', 'remaining_amount', 'completion_percentage',
            'payment_status', 'is_fully_paid', 'is_partially_paid',
            'actual_payments_count', 'paid_by_users', 'my_share', 'other_share',
            # Campi ricorrenza
            'is_recurring', 'total_installments', 'installment_number',
            'parent_recurring_id', 'recurring_frequency'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_paid', 'remaining_amount',
            'completion_percentage', 'payment_status', 'is_fully_paid',
            'is_partially_paid', 'actual_payments_count', 'paid_by_users', 'my_share', 'other_share'
        ]

    def get_total_paid(self, obj):
        """Importo totale già pagato"""
        return str(obj.get_total_paid())

    def get_remaining_amount(self, obj):
        """Importo rimanente da pagare"""
        return str(obj.get_remaining_amount())

    def get_completion_percentage(self, obj):
        """Percentuale di completamento"""
        return obj.get_completion_percentage()

    def get_payment_status(self, obj):
        """Stato del pagamento"""
        return obj.get_payment_status()

    def get_is_fully_paid(self, obj):
        """Se completamente pagata"""
        return obj.is_fully_paid()

    def get_is_partially_paid(self, obj):
        """Se parzialmente pagata"""
        return obj.is_partially_paid()

    def get_actual_payments_count(self, obj):
        """Numero di pagamenti effettuati"""
        return obj.get_related_expenses().count()

    def get_paid_by_users(self, obj):
        """Restituisce gli utenti che hanno pagato le spese collegate"""
        expenses = obj.get_related_expenses()
        users = []
        user_names = set()

        for expense in expenses:
            if expense.user and expense.user.get_full_name() not in user_names:
                user_names.add(expense.user.get_full_name())
                users.append({
                    'id': expense.user.id,
                    'first_name': expense.user.first_name,
                    'last_name': expense.user.last_name,
                    'full_name': expense.user.get_full_name(),
                    'amount_paid': str(expense.amount)
                })

        return users

    def get_my_share(self, obj):
        """Calcola la quota da pagare"""
        return str(obj.get_my_share())

    def get_other_share(self, obj):
        """Calcola la quota dell'altra persona"""
        return str(obj.get_other_share())


class PlannedExpenseLightSerializer(serializers.ModelSerializer):
    """Serializer leggero per le spese pianificate con campi essenziali per il frontend"""
    category_detail = CategorySerializer(source='category', read_only=True)
    subcategory_detail = CategorySerializer(source='subcategory', read_only=True)

    # Campi essenziali per il frontend
    total_paid = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    is_fully_paid = serializers.SerializerMethodField()
    is_partially_paid = serializers.SerializerMethodField()
    actual_payments_count = serializers.SerializerMethodField()
    paid_by_users = serializers.SerializerMethodField()

    # Informazioni sulle rate ricorrenti collegate
    recurring_installments_status = serializers.SerializerMethodField()
    recurring_installments_summary = serializers.SerializerMethodField()
    my_share = serializers.SerializerMethodField()
    other_share = serializers.SerializerMethodField()

    class Meta:
        model = PlannedExpense
        fields = [
            'id', 'spending_plan', 'description', 'amount', 'category', 'category_detail',
            'subcategory', 'subcategory_detail', 'priority', 'due_date',
            'notes', 'is_completed', 'is_hidden', 'payment_type', 'my_share_amount', 'paid_by_user', 'created_at', 'updated_at',
            'total_paid', 'remaining_amount', 'completion_percentage',
            'payment_status', 'is_fully_paid', 'is_partially_paid',
            'actual_payments_count', 'paid_by_users', 'my_share', 'other_share',
            # Campi ricorrenza
            'is_recurring', 'total_installments', 'installment_number',
            'parent_recurring_id', 'recurring_frequency',
            'recurring_installments_status', 'recurring_installments_summary'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_paid', 'remaining_amount',
            'completion_percentage', 'payment_status', 'is_fully_paid',
            'is_partially_paid', 'actual_payments_count', 'paid_by_users', 'recurring_installments_status',
            'recurring_installments_summary', 'my_share', 'other_share'
        ]

    def get_total_paid(self, obj):
        """Importo totale già pagato"""
        return str(obj.get_total_paid())

    def get_remaining_amount(self, obj):
        """Importo rimanente da pagare"""
        return str(obj.get_remaining_amount())

    def get_completion_percentage(self, obj):
        """Percentuale di completamento"""
        return obj.get_completion_percentage()

    def get_payment_status(self, obj):
        """Stato del pagamento"""
        return obj.get_payment_status()

    def get_is_fully_paid(self, obj):
        """Se la spesa è completamente pagata"""
        return obj.is_fully_paid()

    def get_is_partially_paid(self, obj):
        """Se la spesa è parzialmente pagata"""
        return obj.is_partially_paid()

    def get_actual_payments_count(self, obj):
        """Numero di pagamenti effettuati"""
        return obj.actual_payments.count()

    def get_recurring_installments_status(self, obj):
        """Restituisce lo stato di tutte le rate ricorrenti collegate"""
        if not obj.is_recurring or not obj.parent_recurring_id:
            return None

        # Trova tutte le rate collegate usando lo stesso parent_recurring_id
        from apps.reports.models import PlannedExpense
        installments = PlannedExpense.objects.filter(
            parent_recurring_id=obj.parent_recurring_id
        ).order_by('installment_number')

        # Costruisci l'array con lo stato di ogni rata
        installments_data = []
        for installment in installments:
            installments_data.append({
                'installment_number': installment.installment_number,
                'is_completed': installment.is_completed,
                'is_fully_paid': installment.is_fully_paid(),
                'is_partially_paid': installment.is_partially_paid(),
                'due_date': installment.due_date.isoformat() if installment.due_date else None,
                'amount': str(installment.amount)
            })

        return installments_data

    def get_recurring_installments_summary(self, obj):
        """Restituisce la sintesi degli importi delle rate ricorrenti"""
        if not obj.is_recurring or not obj.parent_recurring_id:
            return None

        # Trova tutte le rate collegate usando lo stesso parent_recurring_id
        from apps.reports.models import PlannedExpense
        from decimal import Decimal

        installments = PlannedExpense.objects.filter(
            parent_recurring_id=obj.parent_recurring_id
        )

        # Calcola i totali
        total_amount = Decimal('0.00')
        completed_amount = Decimal('0.00')
        pending_amount = Decimal('0.00')

        for installment in installments:
            amount = installment.amount or Decimal('0.00')
            total_amount += amount

            if installment.is_completed or installment.is_fully_paid():
                completed_amount += amount
            else:
                pending_amount += amount

        return {
            'total_amount': str(total_amount),
            'completed_amount': str(completed_amount),
            'pending_amount': str(pending_amount),
            'total_count': installments.count()
        }

    def get_paid_by_users(self, obj):
        """Restituisce gli utenti che hanno pagato le spese collegate"""
        expenses = obj.get_related_expenses()
        users = []
        user_names = set()

        for expense in expenses:
            if expense.user and expense.user.get_full_name() not in user_names:
                user_names.add(expense.user.get_full_name())
                users.append({
                    'id': expense.user.id,
                    'first_name': expense.user.first_name,
                    'last_name': expense.user.last_name,
                    'full_name': expense.user.get_full_name(),
                    'amount_paid': str(expense.amount)
                })

        return users

    def get_my_share(self, obj):
        """Calcola la quota da pagare"""
        return str(obj.get_my_share())

    def get_other_share(self, obj):
        """Calcola la quota dell'altra persona"""
        return str(obj.get_other_share())


class PlannedExpenseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare spese pianificate"""

    class Meta:
        model = PlannedExpense
        fields = [
            'spending_plan', 'description', 'amount', 'category', 'subcategory',
            'priority', 'due_date', 'notes', 'payment_type', 'my_share_amount', 'paid_by_user',
            # Campi ricorrenza
            'is_recurring', 'total_installments', 'installment_number',
            'parent_recurring_id', 'recurring_frequency'
        ]

    def validate_amount(self, value):
        """Valida che l'importo sia positivo"""
        if value <= 0:
            raise serializers.ValidationError("L'importo deve essere maggiore di zero.")
        return value

    def validate_spending_plan(self, value):
        """Valida che l'utente abbia accesso al piano di spesa"""
        user = self.context['request'].user

        # Se l'utente non ha famiglia, non può accedere a nessun piano
        if not user.family:
            raise serializers.ValidationError("Devi appartenere a una famiglia per creare spese pianificate.")

        # Verifica che il piano di spesa appartenga alla famiglia dell'utente
        family_users = user.family.members.all()
        if not value.users.filter(id__in=family_users).exists():
            raise serializers.ValidationError("Non hai accesso a questo piano di spesa.")

        return value


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer per i budget"""
    users_detail = UserSerializer(source='users', many=True, read_only=True)
    category_budgets = BudgetCategorySerializer(many=True, read_only=True)
    planned_expenses = PlannedExpenseSerializer(many=True, read_only=True)
    total_planned_amount = serializers.SerializerMethodField()
    completed_expenses_amount = serializers.SerializerMethodField()
    pending_expenses_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'description', 'plan_type', 'start_date', 'end_date',
            'users', 'users_detail', 'is_active', 'category_budgets',
            'planned_expenses', 'total_planned_amount', 'completed_expenses_amount',
            'pending_expenses_amount', 'completion_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'total_planned_amount', 'completed_expenses_amount', 'pending_expenses_amount', 'completion_percentage'
        ]

    def get_total_planned_amount(self, obj):
        """Restituisce l'importo totale pianificato"""
        return str(obj.get_total_planned_amount())

    def get_completed_expenses_amount(self, obj):
        """Restituisce l'importo delle spese completate"""
        return str(obj.get_completed_expenses_amount())

    def get_pending_expenses_amount(self, obj):
        """Restituisce l'importo delle spese in sospeso"""
        return str(obj.get_pending_expenses_amount())

    def get_completion_percentage(self, obj):
        """Restituisce la percentuale di completamento"""
        return float(obj.get_completion_percentage())


class BudgetCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare budget"""
    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserSerializer.Meta.model.objects.all()
    )

    class Meta:
        model = Budget
        fields = [
            'name', 'description', 'plan_type', 'start_date', 'end_date',
            'users', 'is_active'
        ]

    def validate(self, attrs):
        """Valida che non esista già un budget per lo stesso periodo"""
        name = attrs.get('name')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        # Valida che end_date sia dopo start_date
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                "end_date": "La data di fine deve essere successiva alla data di inizio."
            })

        if self.instance:
            # In caso di aggiornamento
            if Budget.objects.exclude(pk=self.instance.pk).filter(
                name=name, start_date=start_date, end_date=end_date
            ).exists():
                raise serializers.ValidationError(
                    "Esiste già un budget con questo nome per il periodo selezionato."
                )
        else:
            # In caso di creazione
            if Budget.objects.filter(name=name, start_date=start_date, end_date=end_date).exists():
                raise serializers.ValidationError(
                    "Esiste già un budget con questo nome per il periodo selezionato."
                )

        return attrs


class BudgetCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare categorie di budget"""

    class Meta:
        model = BudgetCategory
        fields = ['budget', 'category', 'amount']

    def validate(self, attrs):
        """Verifica che non esista già una categoria per questo budget"""
        budget = attrs.get('budget')
        category = attrs.get('category')

        if self.instance:
            # In caso di aggiornamento
            if BudgetCategory.objects.exclude(pk=self.instance.pk).filter(
                budget=budget, category=category
            ).exists():
                raise serializers.ValidationError(
                    "Questa categoria è già presente nel budget."
                )
        else:
            # In caso di creazione
            if BudgetCategory.objects.filter(budget=budget, category=category).exists():
                raise serializers.ValidationError(
                    "Questa categoria è già presente nel budget."
                )

        return attrs


class SavingGoalSerializer(serializers.ModelSerializer):
    """Serializer per gli obiettivi di risparmio"""
    users_detail = UserSerializer(source='users', many=True, read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = SavingGoal
        fields = [
            'id', 'name', 'description', 'target_amount', 'current_amount',
            'target_date', 'users', 'users_detail', 'is_completed',
            'progress_percentage', 'remaining_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'progress_percentage', 'remaining_amount'
        ]

    def get_progress_percentage(self, obj):
        """Restituisce la percentuale di progresso"""
        return float(obj.get_progress_percentage())

    def get_remaining_amount(self, obj):
        """Restituisce l'importo rimanente"""
        return str(obj.get_remaining_amount())


class SavingGoalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare obiettivi di risparmio"""
    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserSerializer.Meta.model.objects.all()
    )

    class Meta:
        model = SavingGoal
        fields = [
            'name', 'description', 'target_amount', 'current_amount',
            'target_date', 'users', 'is_completed'
        ]

    def validate(self, attrs):
        """Valida gli importi"""
        target_amount = attrs.get('target_amount')
        current_amount = attrs.get('current_amount', 0)

        if current_amount > target_amount:
            raise serializers.ValidationError({
                "current_amount": "L'importo attuale non può superare l'importo obiettivo."
            })

        return attrs


class SpendingPlanSerializer(serializers.ModelSerializer):
    """Serializer per i piani di spesa"""
    users_detail = UserSerializer(source='users', many=True, read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    planned_expenses = PlannedExpenseSerializer(many=True, read_only=True)

    # Statistiche calcolate dal backend
    total_planned_amount = serializers.SerializerMethodField()
    total_unplanned_expenses_amount = serializers.SerializerMethodField()
    total_estimated_amount = serializers.SerializerMethodField()
    completed_expenses_amount = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    total_expenses_count = serializers.SerializerMethodField()
    pending_expenses_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    is_pinned_by_user = serializers.BooleanField(read_only=True, required=False)

    class Meta:
        model = SpendingPlan
        fields = [
            'id', 'name', 'description', 'plan_type', 'plan_scope', 'start_date', 'end_date', 'total_budget',
            'users', 'users_detail', 'is_shared', 'created_by', 'created_by_detail',
            'is_active', 'is_hidden', 'is_pinned', 'is_pinned_by_user', 'auto_generated', 'planned_expenses',
            'total_planned_amount', 'total_unplanned_expenses_amount', 'total_estimated_amount',
            'completed_expenses_amount', 'completed_count', 'total_expenses_count',
            'pending_expenses_amount', 'completion_percentage', 'is_current',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_planned_amount',
            'total_unplanned_expenses_amount', 'total_estimated_amount',
            'completed_expenses_amount', 'completed_count', 'total_expenses_count',
            'pending_expenses_amount', 'completion_percentage', 'is_current'
        ]

    def get_total_planned_amount(self, obj):
        """Importo totale pianificato"""
        return str(obj.get_total_planned_amount())

    def get_total_unplanned_expenses_amount(self, obj):
        """Importo totale spese non pianificate"""
        return str(obj.get_total_unplanned_expenses_amount())

    def get_total_estimated_amount(self, obj):
        """Importo totale stimato (pianificate + non pianificate)"""
        return str(obj.get_total_estimated_amount())

    def get_completed_expenses_amount(self, obj):
        """Importo delle spese completate"""
        return str(obj.get_completed_expenses_amount())

    def get_completed_count(self, obj):
        """Numero di spese completate"""
        return obj.get_completed_count()

    def get_total_expenses_count(self, obj):
        """Numero totale di spese"""
        return obj.get_total_expenses_count()

    def get_pending_expenses_amount(self, obj):
        """Importo delle spese in sospeso"""
        return str(obj.get_pending_expenses_amount())

    def get_completion_percentage(self, obj):
        """Percentuale di completamento"""
        return float(obj.get_completion_percentage())

    def get_is_current(self, obj):
        """Se il piano è attivo nel periodo corrente"""
        return obj.is_current()


class SpendingPlanDetailSerializer(serializers.ModelSerializer):
    """Serializer ottimizzato per i dettagli del piano (endpoint /details/)"""
    users_detail = UserSerializer(source='users', many=True, read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    planned_expenses_detail = PlannedExpenseLightSerializer(source='planned_expenses', many=True, read_only=True)

    # Statistiche calcolate dal backend
    total_planned_amount = serializers.SerializerMethodField()
    total_unplanned_expenses_amount = serializers.SerializerMethodField()
    total_estimated_amount = serializers.SerializerMethodField()
    completed_expenses_amount = serializers.SerializerMethodField()
    pending_expenses_amount = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()
    total_expenses_count = serializers.SerializerMethodField()

    class Meta:
        model = SpendingPlan
        fields = [
            'id', 'name', 'description', 'plan_type', 'plan_scope', 'start_date', 'end_date',
            'total_budget', 'users', 'users_detail', 'is_shared', 'is_active',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'planned_expenses_detail',
            'total_planned_amount', 'total_unplanned_expenses_amount', 'total_estimated_amount',
            'completed_expenses_amount', 'pending_expenses_amount', 'completion_percentage',
            'completed_count', 'total_expenses_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_planned_amount',
            'total_unplanned_expenses_amount', 'total_estimated_amount',
            'completed_expenses_amount', 'pending_expenses_amount',
            'completion_percentage', 'completed_count', 'total_expenses_count'
        ]

    def get_total_planned_amount(self, obj):
        return str(obj.get_total_planned_amount())

    def get_total_unplanned_expenses_amount(self, obj):
        return str(obj.get_total_unplanned_expenses_amount())

    def get_total_estimated_amount(self, obj):
        return str(obj.get_total_estimated_amount())

    def get_completed_expenses_amount(self, obj):
        return str(obj.get_completed_expenses_amount())

    def get_pending_expenses_amount(self, obj):
        return str(obj.get_pending_expenses_amount())

    def get_completion_percentage(self, obj):
        return float(obj.get_completion_percentage())

    def get_completed_count(self, obj):
        return obj.get_completed_count()

    def get_total_expenses_count(self, obj):
        return obj.get_total_expenses_count()


class SpendingPlanListSerializer(serializers.ModelSerializer):
    """Serializer ULTRA-LEGGERO per la lista dei piani - evita N+1 query"""
    from decimal import Decimal

    # Usa valori già annotati dal queryset (NO query extra!)
    total_planned_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=True
    )
    completed_expenses_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=True
    )
    unplanned_expenses_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=True
    )
    planned_expenses_count = serializers.IntegerField(read_only=True)
    unplanned_expenses_count = serializers.IntegerField(read_only=True)
    completed_count = serializers.IntegerField(read_only=True)

    # Calcoli semplici senza query
    total_estimated_amount = serializers.SerializerMethodField()
    total_expenses_count = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()
    pending_expenses_amount = serializers.SerializerMethodField()

    # Solo ID utenti (no nested serializer pesante)
    user_ids = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    # Campi essenziali del piano
    is_current = serializers.SerializerMethodField()
    is_shared = serializers.SerializerMethodField()

    # Pin personalizzato per l'utente (dal queryset annotato)
    is_pinned_by_user = serializers.BooleanField(read_only=True)

    class Meta:
        model = SpendingPlan
        fields = [
            'id', 'name', 'description', 'plan_type', 'plan_scope',
            'start_date', 'end_date', 'total_budget',
            'total_planned_amount', 'completed_expenses_amount',
            'unplanned_expenses_amount', 'planned_expenses_count',
            'unplanned_expenses_count', 'completed_count',
            'total_estimated_amount', 'total_expenses_count', 'completion_percentage',
            'pending_expenses_amount',
            'user_ids', 'created_by_name', 'is_active', 'is_hidden',
            'is_pinned', 'is_pinned_by_user', 'auto_generated', 'is_current', 'is_shared',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'total_planned_amount', 'completed_expenses_amount',
            'unplanned_expenses_amount', 'planned_expenses_count',
            'unplanned_expenses_count', 'completed_count'
        ]

    def get_total_estimated_amount(self, obj):
        """Calcola totale stimato da valori annotati"""
        from decimal import Decimal
        planned = obj.total_planned_amount or Decimal('0.00')
        unplanned = obj.unplanned_expenses_amount or Decimal('0.00')
        return str(planned + unplanned)

    def get_total_expenses_count(self, obj):
        """Calcola totale spese da valori annotati"""
        planned = getattr(obj, 'planned_expenses_count', 0) or 0
        unplanned = getattr(obj, 'unplanned_expenses_count', 0) or 0
        return planned + unplanned

    def get_pending_expenses_amount(self, obj):
        """Calcola importo rimanente da valori annotati"""
        from decimal import Decimal
        total = obj.total_planned_amount or Decimal('0.00')
        completed = obj.completed_expenses_amount or Decimal('0.00')
        return str(max(total - completed, Decimal('0.00')))

    def get_completion_percentage(self, obj):
        """Calcola percentuale completamento da valori annotati"""
        from decimal import Decimal
        total = obj.total_planned_amount or Decimal('0.00')
        completed = obj.completed_expenses_amount or Decimal('0.00')

        if total > 0:
            return float((completed / total) * 100)
        return 0.0

    def get_user_ids(self, obj):
        """Usa prefetch_related esistente (no query extra)"""
        return [u.id for u in obj.users.all()]

    def get_is_current(self, obj):
        """Verifica se il piano è attivo nel periodo corrente"""
        from django.utils import timezone
        today = timezone.now().date()
        return obj.start_date <= today <= obj.end_date

    def get_is_shared(self, obj):
        """Verifica se il piano è condiviso (familiare)"""
        return obj.plan_scope == 'family'


class SpendingPlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare piani di spesa"""
    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserSerializer.Meta.model.objects.all()
    )

    class Meta:
        model = SpendingPlan
        fields = [
            'name', 'description', 'plan_type', 'plan_scope', 'start_date', 'end_date', 'total_budget',
            'users', 'is_active', 'is_hidden', 'auto_generated'
        ]

    def validate(self, attrs):
        """Valida le date"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                "end_date": "La data di fine deve essere successiva alla data di inizio."
            })

        return attrs
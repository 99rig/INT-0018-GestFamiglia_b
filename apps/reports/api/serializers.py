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

    class Meta:
        model = PlannedExpense
        fields = [
            'id', 'spending_plan', 'description', 'amount', 'category', 'category_detail',
            'subcategory', 'subcategory_detail', 'priority', 'due_date',
            'notes', 'is_completed', 'created_at', 'updated_at',
            'total_paid', 'remaining_amount', 'completion_percentage',
            'payment_status', 'is_fully_paid', 'is_partially_paid',
            'actual_payments_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_paid', 'remaining_amount',
            'completion_percentage', 'payment_status', 'is_fully_paid',
            'is_partially_paid', 'actual_payments_count'
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


class PlannedExpenseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare spese pianificate"""

    class Meta:
        model = PlannedExpense
        fields = [
            'spending_plan', 'description', 'amount', 'category', 'subcategory',
            'priority', 'due_date', 'notes'
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
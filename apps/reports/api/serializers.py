from rest_framework import serializers
from apps.reports.models import Budget, BudgetCategory, SavingGoal
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


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer per i budget"""
    users_detail = UserSerializer(source='users', many=True, read_only=True)
    category_budgets = BudgetCategorySerializer(many=True, read_only=True)
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'description', 'year', 'month', 'total_amount',
            'users', 'users_detail', 'is_active', 'category_budgets',
            'spent_amount', 'remaining_amount', 'percentage_used',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'spent_amount', 'remaining_amount', 'percentage_used'
        ]
    
    def get_spent_amount(self, obj):
        """Restituisce l'importo speso"""
        return str(obj.get_spent_amount())
    
    def get_remaining_amount(self, obj):
        """Restituisce l'importo rimanente"""
        return str(obj.get_remaining_amount())
    
    def get_percentage_used(self, obj):
        """Restituisce la percentuale utilizzata"""
        return float(obj.get_percentage_used())


class BudgetCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare budget"""
    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserSerializer.Meta.model.objects.all()
    )
    
    class Meta:
        model = Budget
        fields = [
            'name', 'description', 'year', 'month',
            'total_amount', 'users', 'is_active'
        ]
    
    def validate(self, attrs):
        """Valida che non esista già un budget per lo stesso periodo"""
        name = attrs.get('name')
        year = attrs.get('year')
        month = attrs.get('month')
        
        if self.instance:
            # In caso di aggiornamento
            if Budget.objects.exclude(pk=self.instance.pk).filter(
                name=name, year=year, month=month
            ).exists():
                raise serializers.ValidationError(
                    "Esiste già un budget con questo nome per il periodo selezionato."
                )
        else:
            # In caso di creazione
            if Budget.objects.filter(name=name, year=year, month=month).exists():
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
                "current_amount": "L'importo attuale non pu� superare l'importo obiettivo."
            })
        
        return attrs
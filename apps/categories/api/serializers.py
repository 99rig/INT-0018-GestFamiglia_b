from rest_framework import serializers
from apps.categories.models import Category, Subcategory


class SubcategorySerializer(serializers.ModelSerializer):
    """Serializer per le sottocategorie"""
    
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer per le categorie"""
    subcategories = SubcategorySerializer(many=True, read_only=True)
    expense_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'type', 'icon', 'color',
            'monthly_budget', 'is_active', 'subcategories',
            'expense_count', 'total_spent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expense_count', 'total_spent']
    
    def get_expense_count(self, obj):
        """Conta il numero di spese per questa categoria"""
        return obj.expenses.count()
    
    def get_total_spent(self, obj):
        """Calcola il totale speso per questa categoria"""
        from django.db.models import Sum
        total = obj.expenses.filter(status='pagata').aggregate(
            total=Sum('amount')
        )['total']
        return str(total) if total else "0.00"


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare categorie"""
    
    class Meta:
        model = Category
        fields = [
            'name', 'description', 'type', 'icon', 'color',
            'monthly_budget', 'is_active'
        ]
    
    def validate_color(self, value):
        """Valida il formato del colore HEX"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError(
                "Il colore deve essere in formato HEX (es. #FF5733)"
            )
        return value


class SubcategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer per creare/aggiornare sottocategorie"""
    
    class Meta:
        model = Subcategory
        fields = ['category', 'name', 'description', 'is_active']
    
    def validate(self, attrs):
        """Verifica unicità del nome nella categoria"""
        category = attrs.get('category')
        name = attrs.get('name')
        
        if self.instance:
            # In caso di aggiornamento
            if Subcategory.objects.exclude(pk=self.instance.pk).filter(
                category=category, name=name
            ).exists():
                raise serializers.ValidationError({
                    "name": "Una sottocategoria con questo nome esiste già in questa categoria."
                })
        else:
            # In caso di creazione
            if Subcategory.objects.filter(category=category, name=name).exists():
                raise serializers.ValidationError({
                    "name": "Una sottocategoria con questo nome esiste già in questa categoria."
                })
        
        return attrs
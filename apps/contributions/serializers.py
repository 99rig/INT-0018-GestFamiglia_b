from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Contribution, ExpenseContribution, FamilyBalance
from apps.users.api.serializers import UserProfileSerializer

User = get_user_model()


class ContributionSerializer(serializers.ModelSerializer):
    user_detail = UserProfileSerializer(source='user', read_only=True)
    used_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    usage_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = Contribution
        fields = [
            'id', 'user', 'user_detail', 'amount', 'available_balance',
            'description', 'contribution_type', 'date', 'notes', 'status',
            'family', 'used_amount', 'usage_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'available_balance', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Imposta automaticamente la famiglia dell'utente
        user = validated_data['user']
        if hasattr(user, 'family') and user.family:
            validated_data['family'] = user.family
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['used_amount'] = instance.get_used_amount()
        data['usage_percentage'] = instance.get_usage_percentage()
        return data


class ContributionListSerializer(serializers.ModelSerializer):
    """Serializer leggero per liste"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Contribution
        fields = [
            'id', 'user', 'user_name', 'amount', 'available_balance',
            'description', 'contribution_type', 'date', 'status'
        ]


class ExpenseContributionSerializer(serializers.ModelSerializer):
    contribution_detail = ContributionListSerializer(source='contribution', read_only=True)
    expense_description = serializers.CharField(source='expense.description', read_only=True)

    class Meta:
        model = ExpenseContribution
        fields = [
            'id', 'expense', 'expense_description', 'contribution',
            'contribution_detail', 'amount_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FamilyBalanceSerializer(serializers.ModelSerializer):
    family_name = serializers.CharField(source='family.name', read_only=True)

    class Meta:
        model = FamilyBalance
        fields = [
            'id', 'family', 'family_name', 'total_contributions',
            'total_expenses', 'current_balance', 'last_updated'
        ]
        read_only_fields = ['id', 'total_contributions', 'total_expenses', 'current_balance', 'last_updated']


class ContributionStatsSerializer(serializers.Serializer):
    """Serializer per statistiche contributi"""
    total_contributions = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_available = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_used = serializers.DecimalField(max_digits=12, decimal_places=2)
    contributors_count = serializers.IntegerField()
    recent_contributions = ContributionListSerializer(many=True)
    top_contributors = serializers.ListField()
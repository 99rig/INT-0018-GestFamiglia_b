from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Contribution, ExpenseContribution, FamilyBalance
from .serializers import (
    ContributionSerializer,
    ContributionListSerializer,
    ExpenseContributionSerializer,
    FamilyBalanceSerializer,
    ContributionStatsSerializer
)


class ContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint per la gestione dei contributi famiglia
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ContributionSerializer

    def get_queryset(self):
        """Filtra i contributi per famiglia dell'utente"""
        user = self.request.user
        queryset = Contribution.objects.all()

        # Filtra per famiglia dell'utente
        if hasattr(user, 'family') and user.family:
            queryset = queryset.filter(
                Q(family=user.family) | Q(user=user)
            ).distinct()
        else:
            queryset = queryset.filter(user=user)

        # Filtri opzionali dai query params
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        user_filter = self.request.query_params.get('user', None)
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)

        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset.order_by('-date', '-created_at')

    def get_serializer_class(self):
        """Usa serializer diversi per list e detail"""
        if self.action == 'list':
            return ContributionListSerializer
        return ContributionSerializer

    def perform_create(self, serializer):
        """Imposta l'utente corrente come contributore"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiche sui contributi della famiglia"""
        user = request.user
        queryset = self.get_queryset()

        # Calcola statistiche
        stats = queryset.aggregate(
            total_contributions=Sum('amount') or Decimal('0.00'),
            total_available=Sum('available_balance') or Decimal('0.00')
        )

        stats['total_used'] = stats['total_contributions'] - stats['total_available']
        stats['contributors_count'] = queryset.values('user').distinct().count()

        # Ultimi 5 contributi
        stats['recent_contributions'] = queryset[:5]

        # Top 3 contributori
        top_contributors = queryset.values('user__id', 'user__first_name', 'user__last_name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:3]
        stats['top_contributors'] = list(top_contributors)

        serializer = ContributionStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Saldo complessivo della famiglia"""
        user = request.user
        if not hasattr(user, 'family') or not user.family:
            return Response(
                {"detail": "Utente non associato a una famiglia"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crea o aggiorna il saldo famiglia
        balance, created = FamilyBalance.objects.get_or_create(
            family=user.family
        )
        balance.update_balance()

        serializer = FamilyBalanceSerializer(balance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def use_for_expense(self, request, pk=None):
        """Utilizza il contributo per una spesa"""
        contribution = self.get_object()
        amount = Decimal(request.data.get('amount', '0.00'))
        expense_id = request.data.get('expense_id')

        if not expense_id:
            return Response(
                {"detail": "ID spesa richiesto"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {"detail": "L'importo deve essere maggiore di zero"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount > contribution.available_balance:
            return Response(
                {"detail": f"Importo richiesto ({amount}) superiore al saldo disponibile ({contribution.available_balance})"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.expenses.models import Expense
            expense = Expense.objects.get(id=expense_id)

            # Crea il collegamento spesa-contributo
            expense_contribution = ExpenseContribution.objects.create(
                expense=expense,
                contribution=contribution,
                amount_used=amount
            )

            # Aggiorna il saldo del contributo
            contribution.use_amount(amount)

            serializer = ExpenseContributionSerializer(expense_contribution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Expense.DoesNotExist:
            return Response(
                {"detail": "Spesa non trovata"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Lista contributi con saldo disponibile"""
        queryset = self.get_queryset().filter(
            available_balance__gt=0
        ).order_by('-available_balance')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExpenseContributionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint per visualizzare l'utilizzo dei contributi
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseContributionSerializer

    def get_queryset(self):
        """Filtra per famiglia dell'utente"""
        user = self.request.user
        queryset = ExpenseContribution.objects.all()

        if hasattr(user, 'family') and user.family:
            queryset = queryset.filter(
                contribution__family=user.family
            )
        else:
            queryset = queryset.filter(
                Q(contribution__user=user) | Q(expense__user=user)
            ).distinct()

        # Filtri opzionali
        expense_id = self.request.query_params.get('expense', None)
        if expense_id:
            queryset = queryset.filter(expense_id=expense_id)

        contribution_id = self.request.query_params.get('contribution', None)
        if contribution_id:
            queryset = queryset.filter(contribution_id=contribution_id)

        return queryset.order_by('-created_at')

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    MCFTokenObtainPairSerializer,
    FamilySerializer,
    FamilyCreateSerializer,
    FamilyInvitationSerializer,
    FamilyInvitationCreateSerializer,
    JoinFamilySerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione degli utenti"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Permette la registrazione senza autenticazione"""
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Restituisce i dati dell'utente corrente"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambia la password dell'utente corrente"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {'detail': 'Password cambiata con successo.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def family_members(self, request):
        """Restituisce tutti i membri della stessa famiglia"""
        user = request.user

        # Se l'utente non appartiene a nessuna famiglia, restituisce lista vuota
        if not user.family:
            return Response([])

        # Filtra solo i membri della stessa famiglia
        family_users = user.family.members.filter(is_active=True).exclude(id=user.id)
        serializer = UserSerializer(family_users, many=True)
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    """View per la registrazione di nuovi utenti"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View per visualizzare e aggiornare il profilo utente"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Esegui l'aggiornamento
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # Refresh dal database per assicurarsi di avere i dati più recenti
        updated_instance.refresh_from_db()
        if hasattr(updated_instance, 'profile'):
            updated_instance.profile.refresh_from_db()

        # Per la risposta, usa UserSerializer per includere il profilo completo
        response_serializer = UserSerializer(updated_instance)
        return Response(response_serializer.data)


class MCFTokenObtainPairView(TokenObtainPairView):
    """Vista di login personalizzata con dati utente"""
    serializer_class = MCFTokenObtainPairSerializer


class LogoutView(generics.GenericAPIView):
    """Vista per il logout (JWT stateless, non c'è molto da fare)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(
            {'detail': 'Logout effettuato con successo.'},
            status=status.HTTP_200_OK
        )


class FamilyViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione delle famiglie"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restituisce solo la famiglia dell'utente corrente"""
        user = self.request.user
        if user.family:
            return user.family.__class__.objects.filter(id=user.family.id)
        return user.family.__class__.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return FamilyCreateSerializer
        return FamilySerializer

    @action(detail=False, methods=['post'])
    def join(self, request):
        """Unisciti a una famiglia tramite codice invito"""
        serializer = JoinFamilySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            family = serializer.save()
            family_serializer = FamilySerializer(family)
            return Response(
                {
                    'detail': f'Ti sei unito alla famiglia "{family.name}" con successo!',
                    'family': family_serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def leave(self, request):
        """Lascia la famiglia corrente"""
        user = request.user
        if not user.family:
            return Response(
                {'detail': 'Non sei membro di nessuna famiglia.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        family_name = user.family.name
        user.family = None
        user.save()

        return Response(
            {'detail': f'Hai lasciato la famiglia "{family_name}" con successo.'},
            status=status.HTTP_200_OK
        )


class FamilyInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet per la gestione degli inviti famiglia"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Restituisce gli inviti della famiglia dell'utente"""
        user = self.request.user
        if user.family:
            return user.family.invitations.all()
        return user.family.__class__.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return FamilyInvitationCreateSerializer
        return FamilyInvitationSerializer
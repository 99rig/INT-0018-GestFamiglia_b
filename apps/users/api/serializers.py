from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.users.models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer per il profilo utente"""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'role', 'family_role', 'phone_number', 'birth_date',
            'profile_picture', 'bio', 'is_master', 'can_plan_budget',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_master', 'can_plan_budget', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer per il modello User con profilo"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer per la creazione di nuovi utenti"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    # Campi del profilo
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='familiare')
    family_role = serializers.ChoiceField(choices=UserProfile.FAMILY_ROLE_CHOICES, default='altro')
    phone_number = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'role', 'family_role', 
            'phone_number', 'birth_date', 'bio'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "I campi password non corrispondono."
            })
        return attrs
    
    def create(self, validated_data):
        # Estrae i campi del profilo
        profile_data = {
            'role': validated_data.pop('role', 'familiare'),
            'family_role': validated_data.pop('family_role', 'altro'),
            'phone_number': validated_data.pop('phone_number', ''),
            'birth_date': validated_data.pop('birth_date', None),
            'bio': validated_data.pop('bio', ''),
        }
        
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Crea il profilo
        UserProfile.objects.create(user=user, **profile_data)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer per l'aggiornamento degli utenti"""
    
    # Campi del profilo
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    family_role = serializers.ChoiceField(choices=UserProfile.FAMILY_ROLE_CHOICES, required=False)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'role', 'family_role', 'phone_number', 'birth_date', 
            'profile_picture', 'bio'
        ]
    
    def update(self, instance, validated_data):
        # Estrae i campi del profilo
        profile_data = {}
        profile_fields = ['role', 'family_role', 'phone_number', 'birth_date', 'profile_picture', 'bio']
        
        for field in profile_fields:
            if field in validated_data:
                profile_data[field] = validated_data.pop(field)
        
        # Aggiorna l'utente
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Aggiorna o crea il profilo
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer per il cambio password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "I campi password non corrispondono."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password attuale non corretta.")
        return value


class MCFTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer JWT personalizzato che include i dati utente"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Aggiungi dati personalizzati al token
        token['email'] = user.email
        token['name'] = user.get_full_name()
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Aggiungi dati utente alla risposta
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': user.get_full_name(),
        }
        
        # Aggiungi dati del profilo se esiste
        try:
            profile = user.profile
            data['user']['userprofile'] = {
                'role': profile.role,
                'family_role': profile.family_role,
                'is_master': profile.is_master,
                'can_plan_budget': profile.can_plan_budget,
            }
        except UserProfile.DoesNotExist:
            data['user']['userprofile'] = None
        
        return data
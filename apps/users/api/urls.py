from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.views import APIView
from .views import (
    UserViewSet, RegisterView, UserProfileView, MCFTokenObtainPairView, LogoutView,
    FamilyViewSet, FamilyInvitationViewSet, PasswordResetRequestView, PasswordResetConfirmView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'families', FamilyViewSet, basename='family')
router.register(r'family-invitations', FamilyInvitationViewSet, basename='family-invitation')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', MCFTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('check/', views.check_update, name='check_update'),
    path('download/<int:version_code>/', views.download_apk, name='download_apk'),
    path('latest/download/', views.download_latest_apk, name='download_latest_apk'),
    path('info/', views.app_info, name='app_info'),
]
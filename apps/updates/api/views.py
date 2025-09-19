from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse, Http404
from django.conf import settings
import os

from ..models import AppVersion


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_update(request):
    """Controlla se ci sono aggiornamenti disponibili"""
    
    current_version = request.GET.get('version_code', 0)
    try:
        current_version = int(current_version)
    except (ValueError, TypeError):
        current_version = 0
    
    latest_version = AppVersion.get_latest_version()
    
    if not latest_version:
        return Response({
            'has_update': False,
            'message': 'Nessuna versione disponibile'
        })
    
    has_update = latest_version.is_newer_than(current_version)
    
    response_data = {
        'has_update': has_update,
        'latest_version': {
            'version_name': latest_version.version_name,
            'version_code': latest_version.version_code,
            'release_notes': latest_version.release_notes,
            'is_mandatory': latest_version.is_mandatory,
            'download_url': f'/updates/download/{latest_version.version_code}/',
            'file_size': latest_version.apk_file_size
        } if has_update else None,
        'current_version_code': current_version
    }
    
    return Response(response_data)


@csrf_exempt
def download_apk(request, version_code):
    """Download dell'APK per una specifica versione"""
    
    try:
        app_version = AppVersion.objects.get(version_code=version_code)
    except AppVersion.DoesNotExist:
        raise Http404("Versione non trovata")
    
    if not app_version.apk_file:
        raise Http404("File APK non disponibile")

    # Usa il percorso corretto nella cartella apk_releases
    apk_path = app_version.apk_file_path
    if not apk_path or not os.path.exists(apk_path):
        raise Http404("File APK non trovato sul server")

    response = FileResponse(
        open(apk_path, 'rb'),
        content_type='application/vnd.android.package-archive',
        as_attachment=True,
        filename=f'MyCrazyFamily-v{app_version.version_name}.apk'
    )
    
    return response


@csrf_exempt
def download_latest_apk(request):
    """Download dell'APK dell'ultima versione disponibile"""

    latest_version = AppVersion.objects.order_by('-version_code').first()

    if not latest_version:
        raise Http404("Nessuna versione disponibile")

    if not latest_version.apk_file:
        raise Http404("File APK non disponibile")

    # Usa il percorso corretto nella cartella apk_releases
    apk_path = latest_version.apk_file_path
    if not apk_path or not os.path.exists(apk_path):
        raise Http404("File APK non trovato sul server")

    response = FileResponse(
        open(apk_path, 'rb'),
        content_type='application/vnd.android.package-archive',
        as_attachment=True,
        filename=f'MyCrazyFamily-v{latest_version.version_name}.apk'
    )

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def app_info(request):
    """Informazioni generali sull'app"""
    
    latest_version = AppVersion.get_latest_version()
    
    return Response({
        'app_name': 'My Crazy Family',
        'latest_version': {
            'version_name': latest_version.version_name,
            'version_code': latest_version.version_code,
            'release_date': latest_version.created_at
        } if latest_version else None,
        'update_endpoint': '/api/updates/check/',
        'download_endpoint': '/api/updates/download/'
    })
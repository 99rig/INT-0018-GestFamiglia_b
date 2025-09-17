#!/usr/bin/env python
"""
Script per aggiungere una nuova versione dell'app al database
"""

import os
import sys
import django
from django.core.files import File

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.updates.models import AppVersion

def add_version():
    # Percorso dell'APK
    apk_path = '/home/mas/Documents/MumbleProjects/INT-0018-GestioneSpese/frontend/src-capacitor/android/app/build/outputs/apk/release/MyCrazyFamily-v1.0.4-production.apk'
    
    # Verifica che il file esista
    if not os.path.exists(apk_path):
        print(f"❌ File APK non trovato: {apk_path}")
        return False
    
    print(f"📱 Aggiungendo versione 1.0.5 al database...")
    
    try:
        # Crea nuova versione
        version = AppVersion.objects.create(
            version_name='1.0.5',
            version_code=5,
            release_notes='Versione di produzione con configurazione server corretta e sistema di auto-update completo.',
            is_mandatory=False,
            min_supported_version=1
        )
        
        # Apri e associa il file APK
        with open(apk_path, 'rb') as apk_file:
            version.apk_file.save(
                'MyCrazyFamily-v1.0.5.apk',
                File(apk_file),
                save=True
            )
        
        print(f"✅ Versione {version.version_name} (code: {version.version_code}) aggiunta con successo!")
        print(f"📁 APK salvato in: {version.apk_file.url}")
        print(f"📏 Dimensione file: {version.apk_file.size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante l'aggiunta della versione: {e}")
        return False

if __name__ == '__main__':
    success = add_version()
    sys.exit(0 if success else 1)
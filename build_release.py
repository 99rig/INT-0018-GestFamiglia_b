#!/usr/bin/env python
"""
Script per aggiornare versione e compilare APK completa
"""

import os
import sys
import subprocess
import django
from datetime import datetime
from django.core.files import File

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.updates.models import AppVersion

def run_command(cmd, cwd=None, description=""):
    """Esegue un comando e gestisce errori"""
    print(f"\n🔧 {description}")
    print(f"📁 Directory: {cwd or 'current'}")
    print(f"🚀 Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore: {e}")
        if e.stdout:
            print(f"📤 Stdout: {e.stdout}")
        if e.stderr:
            print(f"📥 Stderr: {e.stderr}")
        return False

def main():
    print("🚀 BUILD RELEASE My Crazy Family")
    print("=" * 60)
    
    # Ask for build type
    import sys
    build_type = input("🤔 Build type? (dev/prod) [dev]: ").lower().strip() or 'dev'
    
    if build_type not in ['dev', 'prod']:
        print("❌ Invalid build type. Use 'dev' or 'prod'")
        return
    
    # Trova versione successiva
    latest = AppVersion.objects.order_by('-version_code').first()
    new_version_code = (latest.version_code + 1) if latest else 6
    new_version_name = f"1.0.{new_version_code}"
    
    print(f"🔢 Compilando versione: {new_version_name} (code: {new_version_code})")
    print(f"🎯 Build type: {build_type}")
    
    # Directories
    frontend_dir = "/home/mas/Documents/MumbleProjects/INT-0018-GestioneSpese/frontend"
    android_dir = f"{frontend_dir}/src-capacitor/android"
    
    # 1. Build Quasar with environment
    if build_type == 'prod':
        build_cmd = "quasar build -m spa --target prod"
    else:
        build_cmd = "quasar build -m spa"
    
    if not run_command(build_cmd, cwd=frontend_dir, 
                      description=f"Building Quasar app ({build_type})"):
        return
    
    # 2. Copy to Capacitor 
    if not run_command("cp -r dist/spa/* src-capacitor/www/", cwd=frontend_dir,
                      description="Copying build to Capacitor www"):
        return
    
    # 3. Build Android
    if not run_command("./gradlew assembleRelease", cwd=android_dir,
                      description="Building Android APK"):
        return
    
    # 4. Sign APK
    apk_unsigned = f"{android_dir}/app/build/outputs/apk/release/app-release-unsigned.apk"
    apk_signed = f"{android_dir}/app/build/outputs/apk/release/MyCrazyFamily-v{new_version_name}.apk"
    keystore = f"{android_dir}/my-release-key.keystore"
    
    sign_cmd = f"""jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
-keystore {keystore} -storepass marchelo05 {apk_unsigned} alias_name"""
    
    if not run_command(sign_cmd, description="Signing APK"):
        return
    
    # 5. Align APK
    align_cmd = f"""~/Android/Sdk/build-tools/36.0.0/zipalign -v 4 \
{apk_unsigned} {apk_signed}"""
    
    if not run_command(align_cmd, description="Aligning APK"):
        return
    
    # 6. Crea versione nel database
    print(f"\n📱 Creando versione {new_version_name} nel database...")
    try:
        env_info = "produzione" if build_type == 'prod' else "sviluppo"
        version = AppVersion.objects.create(
            version_name=new_version_name,
            version_code=new_version_code,
            release_notes=f'Versione {new_version_name} per {env_info} con icona refresh e configurazione domini.',
            is_mandatory=False,
            min_supported_version=1
        )
        
        # 7. Carica APK
        if os.path.exists(apk_signed):
            with open(apk_signed, 'rb') as apk_file:
                version.apk_file.save(
                    f'MyCrazyFamily-v{new_version_name}.apk',
                    File(apk_file),
                    save=True
                )
            
            print(f"✅ APK caricato nel backend!")
            print(f"📁 URL: {version.apk_file.url}")
            print(f"📏 Size: {version.apk_file.size} bytes")
        else:
            print(f"❌ APK non trovato: {apk_signed}")
            return
        
    except Exception as e:
        print(f"❌ Errore database: {e}")
        return
    
    print("\n🎉 COMPLETATO CON SUCCESSO!")
    print("=" * 60)
    print(f"✅ Versione: {new_version_name}")
    print(f"✅ APK: {apk_signed}")
    print(f"✅ Backend aggiornato")
    print("\n📲 APK pronto per l'installazione!")

if __name__ == '__main__':
    main()
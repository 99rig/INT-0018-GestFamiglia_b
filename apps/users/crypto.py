"""
Utility functions for encrypting/decrypting user data
Using Fernet (symmetric encryption) from cryptography library
"""

import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class UserCrypto:
    """
    Gestisce la crittografia/decrittografia dei dati utente
    Usa AES-256 via Fernet con chiave derivata da password famiglia
    """

    # Salt fisso per la derivazione della chiave famiglia
    # In produzione, questo dovrebbe essere configurabile per famiglia
    FAMILY_SALT = b'mcf-family-salt-2024-v1'

    @classmethod
    def derive_family_key(cls, password: str) -> bytes:
        """
        Deriva una chiave di crittografia dalla password famiglia

        Args:
            password: Password della famiglia (stringa)

        Returns:
            bytes: Chiave di crittografia derivata (32 bytes)
        """
        try:
            # Converte la password in bytes
            password_bytes = password.encode('utf-8')

            # Deriva la chiave usando PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bit key
                salt=cls.FAMILY_SALT,
                iterations=100000,  # 100k iterazioni per sicurezza
            )

            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            return key

        except Exception as e:
            logger.error(f"Error deriving family key: {e}")
            raise ValueError("Failed to derive encryption key")

    @classmethod
    def encrypt_data(cls, data: dict, family_key: bytes) -> str:
        """
        Crittografa un dizionario di dati

        Args:
            data: Dizionario con i dati da crittografare
            family_key: Chiave di crittografia derivata

        Returns:
            str: Dati crittografati (base64 encoded)
        """
        try:
            # Serializza i dati in JSON
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            data_bytes = json_data.encode('utf-8')

            # Critta i dati
            fernet = Fernet(family_key)
            encrypted_data = fernet.encrypt(data_bytes)

            # Ritorna come stringa base64
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise ValueError("Failed to encrypt data")

    @classmethod
    def decrypt_data(cls, encrypted_data: str, family_key: bytes) -> dict:
        """
        Decrittografa i dati crittografati

        Args:
            encrypted_data: Dati crittografati (stringa base64)
            family_key: Chiave di crittografia derivata

        Returns:
            dict: Dati decrittografati
        """
        try:
            # Decodifica da base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))

            # Decrittografa
            fernet = Fernet(family_key)
            decrypted_bytes = fernet.decrypt(encrypted_bytes)

            # Deserializza da JSON
            json_data = decrypted_bytes.decode('utf-8')
            return json.loads(json_data)

        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise ValueError("Failed to decrypt data")

    @classmethod
    def encrypt_user_profile(cls, user, family_password: str) -> bool:
        """
        Crittografa i dati sensibili di un utente

        Args:
            user: Istanza del modello User
            family_password: Password della famiglia

        Returns:
            bool: True se la crittografia è riuscita
        """
        try:
            # Deriva la chiave famiglia
            family_key = cls.derive_family_key(family_password)

            # Raccoglie i dati sensibili
            sensitive_data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

            # Aggiungi dati dal profilo se esistono
            if hasattr(user, 'profile') and user.profile:
                profile = user.profile
                sensitive_data.update({
                    'phone_number': profile.phone_number or '',
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'bio': profile.bio or '',
                })

            # Critta i dati
            encrypted_profile = cls.encrypt_data(sensitive_data, family_key)

            # Salva nel campo encrypted_profile
            user.encrypted_profile = {'data': encrypted_profile}
            user.encryption_version = 1
            user.save(update_fields=['encrypted_profile', 'encryption_version'])

            logger.info(f"Successfully encrypted profile for user {user.id}")
            return True

        except Exception as e:
            logger.error(f"Error encrypting user profile {user.id}: {e}")
            return False

    @classmethod
    def decrypt_user_profile(cls, user, family_password: str) -> dict:
        """
        Decrittografa i dati sensibili di un utente

        Args:
            user: Istanza del modello User
            family_password: Password della famiglia

        Returns:
            dict: Dati decrittografati o dati originali se non crittografati
        """
        try:
            # Se non ha dati crittografati, ritorna i dati originali
            if not user.encrypted_profile or not user.encrypted_profile.get('data'):
                return {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': getattr(user.profile, 'phone_number', '') if hasattr(user, 'profile') else '',
                    'birth_date': getattr(user.profile, 'birth_date', None) if hasattr(user, 'profile') else None,
                    'bio': getattr(user.profile, 'bio', '') if hasattr(user, 'profile') else '',
                }

            # Deriva la chiave famiglia
            family_key = cls.derive_family_key(family_password)

            # Decrittografa i dati
            encrypted_data = user.encrypted_profile['data']
            decrypted_data = cls.decrypt_data(encrypted_data, family_key)

            logger.info(f"Successfully decrypted profile for user {user.id}")
            return decrypted_data

        except Exception as e:
            logger.error(f"Error decrypting user profile {user.id}: {e}")
            # Fallback ai dati originali in caso di errore
            return {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': '',
                'birth_date': None,
                'bio': '',
            }


# Funzioni di convenienza per l'uso rapido
def encrypt_user_data(user, family_password: str) -> bool:
    """Wrapper per crittografare velocemente i dati utente"""
    return UserCrypto.encrypt_user_profile(user, family_password)


def decrypt_user_data(user, family_password: str) -> dict:
    """Wrapper per decrittografare velocemente i dati utente"""
    return UserCrypto.decrypt_user_profile(user, family_password)


def derive_key(password: str) -> bytes:
    """Wrapper per derivare la chiave famiglia"""
    return UserCrypto.derive_family_key(password)
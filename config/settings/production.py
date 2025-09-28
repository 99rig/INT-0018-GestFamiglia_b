# Configurazioni di produzione per Docker

# Configurazioni per produzione - NON sovrascrivere email backend SMTP
# EMAIL_BACKEND rimane quello di base.py (SMTP)

# Frontend URL per email di produzione
FRONTEND_URL = 'https://lacrazyfamily.com/app'

# Database di produzione (PostgreSQL come da docker-compose)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mycrazy',
        'USER': 'postgres',
        'PASSWORD': 'password_from_env',  # Usare variabile ambiente
        'HOST': 'postgres',  # Nome del servizio nel docker-compose
        'PORT': '5432',
    }
}

# Disabilita DEBUG in produzione
DEBUG = False

# Log per debugging email (se necessario)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/email.log',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configurazioni di sicurezza per produzione
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS configurato per il dominio di produzione
CORS_ALLOWED_ORIGINS = [
    "https://lacrazyfamily.com",
    "https://www.lacrazyfamily.com",
]

CORS_ALLOW_CREDENTIALS = True
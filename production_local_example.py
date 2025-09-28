# File local.py per produzione Docker (esempio corretto)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postegres',
        'HOST': 'postgres',
        'PORT': '5432',
    },
    'updates_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'updates.sqlite3',  # noqa: F821
    }
}

# Hosts permessi (aggiungere www se necessario)
ALLOWED_HOSTS = ['lacrazyfamily.com', 'www.lacrazyfamily.com']

# Chiave segreta di produzione (diversa da quella di sviluppo)
SECRET_KEY = "xer6@ah_uju$qa7*!ypzc610ufrq-9vr7snn%5x#w_^fhf2-dw"

# IMPORTANT: NON sovrascrivere EMAIL_BACKEND qui
# Le configurazioni email SMTP sono nel base.py e devono rimanere attive

# Frontend URL per produzione (opzionale, già in base.py)
FRONTEND_URL = 'https://lacrazyfamily.com/app'

# Configurazioni CORS per produzione
CORS_ALLOWED_ORIGINS = [
    "https://lacrazyfamily.com",
    "https://www.lacrazyfamily.com",
]

CORS_ALLOW_CREDENTIALS = True

# Configurazioni di sicurezza
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Gestito da Traefik
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Log per debugging (temporaneo)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/uwsgi/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.users.api.views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Debugging temporaneo per sviluppo
DEBUG = False  # Tenere False in produzione

# Per debugging temporaneo, decommentare:
# DEBUG = True
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
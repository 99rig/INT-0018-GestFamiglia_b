# Guida Debug Password Reset in Produzione

## Problema Identificato
L'errore "Errore durante la richiesta di reset. Riprova." indica che la richiesta API non riesce.

## Possibili Cause e Soluzioni

### 1. Verifica Logs del Container Django
```bash
# Controlla i logs del container Django
docker logs -f lacrazy_django_1

# Oppure se il nome del container è diverso:
docker-compose logs -f django
```

### 2. Verifica Connettività API
```bash
# Test diretto dell'endpoint da dentro il container
docker exec -it lacrazy_django_1 curl -X POST \
  http://localhost:8000/api/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Test dall'esterno (sostituire con il tuo dominio)
curl -X POST https://lacrazyfamily.com/api/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

### 3. Problemi CORS/CSRF più Comuni

#### A. Aggiornare local.py in produzione:
```python
# Aggiungere al tuo /home/docker/lacrazy/local.py:

CORS_ALLOWED_ORIGINS = [
    "https://lacrazyfamily.com",
    "https://www.lacrazyfamily.com",
]

CORS_ALLOW_CREDENTIALS = True

# Configurazioni HTTPS per Traefik
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Gestito da Traefik
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### B. Verifica Headers CORS
Controllare che il frontend invii correttamente gli headers:
- `Content-Type: application/json`
- `X-CSRFToken` (se necessario)

### 4. Test Email SMTP
```python
# Dentro il container Django, test email:
docker exec -it lacrazy_django_1 python manage.py shell

# Nel shell Django:
from django.core.mail import send_mail
from django.conf import settings

try:
    result = send_mail(
        'Test Subject',
        'Test message',
        settings.EMAIL_HOST_USER,
        ['test@example.com'],
        fail_silently=False,
    )
    print(f"Email sent: {result}")
except Exception as e:
    print(f"Email error: {e}")
```

### 5. Verifica Configurazioni Email
Nel file base.py le configurazioni sono:
```python
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'serra.marco@lacrazyfamily.com'
EMAIL_HOST_PASSWORD = 'Mumble100%'
```

**Verificare:**
- Password Zoho ancora valida
- Account non bloccato
- Firewall non blocca porta 587

### 6. Debug Temporaneo

Per debug temporaneo, modificare il local.py aggiungendo:

```python
# SOLO PER DEBUG - rimuovere dopo
DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging dettagliato
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.users.api.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 7. Steps di Debugging Raccomandati

1. **Abilita DEBUG temporaneamente** nel local.py
2. **Riavvia il container:** `docker-compose restart django`
3. **Controlla i logs:** `docker-compose logs -f django`
4. **Testa la richiesta** e osserva i logs
5. **Una volta identificato il problema, disabilita DEBUG**

### 8. Problemi Network più Comuni

#### A. Frontend non raggiunge il backend
- Verifica che Traefik instrada correttamente `/api/` al servizio django
- Controlla che il frontend usi `https://lacrazyfamily.com/api/` come base URL

#### B. Headers mancanti
Il frontend deve inviare:
```javascript
headers: {
  'Content-Type': 'application/json',
  'X-CSRFToken': getCsrfToken(), // se necessario
}
```

### 9. Soluzione Rapida

Se il problema persiste, provare questa configurazione nel local.py:

```python
# Aggiungi queste righe al tuo local.py attuale:

# CORS permissivo (solo per test)
CORS_ALLOW_ALL_ORIGINS = True  # SOLO PER DEBUG
CORS_ALLOW_CREDENTIALS = True

# Headers permessi
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Se il problema persiste, debug email:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**IMPORTANTE:** Rimuovere `CORS_ALLOW_ALL_ORIGINS = True` dopo il debugging!

### 10. Check List Finale

- [ ] Container Django avviato correttamente
- [ ] Logs non mostrano errori 500
- [ ] CORS configurato per il dominio
- [ ] Email SMTP funziona (test manuale)
- [ ] Frontend usa HTTPS per API calls
- [ ] Headers Content-Type corretti
- [ ] Database accessibile

### 11. Contatto per Supporto

Se il problema persiste dopo questi step, fornire:
1. Logs completi del container Django
2. Response HTTP dell'endpoint `/api/auth/password-reset/`
3. Console errors del frontend (F12 → Network tab)
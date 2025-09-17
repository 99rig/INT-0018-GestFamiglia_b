# coding: utf-8
import re

from .base import *  # noqa
try:
    from .logging import *  # noqa
except ImportError:
    pass



from django.utils.crypto import get_random_string

ENABLE_DEBUG_TOOLBAR = False
curdir = os.path.dirname(__file__)
# no longer links in settings.
# we first check ENV, if exists that determines dev/staging/prod
# local.py: retained just for dev and lagacy

if 'ENV' in os.environ:
    settings_env_file = os.path.join(SETTINGS_DIR, os.environ['ENV'] + '.py')  # noqa
else:
    settings_env_file = os.path.join(SETTINGS_DIR, 'settings.py')  # noqa
    if not os.path.exists(settings_env_file):
        print(
            "Imposta ENV o crea il link in web/settings al file di conf: dev/staging o production")
        sys.exit(1)

# Local settings setup, aimed at dev only
local_settings = os.path.join(SETTINGS_DIR, 'local.py')  # noqa
if 'ENV' in os.environ and os.environ['ENV'] == 'dev' and not os.path.exists(local_settings):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    with open(local_settings, 'w') as f:
        f.write('SECRET_KEY = "%s"\n' % get_random_string(50, chars))

# così non è necessario importare dentro local 'from .base *'
# tutto viene gia passato nei 'globals()'
if os.path.exists(settings_env_file):
    with open(settings_env_file) as _f:
        exec(compile(_f.read(), settings_env_file, 'exec'), globals())

if os.path.exists(local_settings):
    with open(local_settings) as _f:
        exec(compile(_f.read(), local_settings, 'exec'), globals())


# if globals().get('SENTRY_DSN_KEY'):  # non cambiare
#     import sentry_sdk
#     from sentry_sdk.integrations.django import DjangoIntegration
#     sentry_sdk.init(
#         dsn=SENTRY_DSN_KEY,
#         integrations=[DjangoIntegration()],
#         send_default_pii=True
#     )

if ENABLE_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_PATCH_SETTINGS = True
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    TEMPLATES[0]['OPTIONS']['context_processors'] += ["django.template.context_processors.debug"]
    MIDDLEWARE[0:0] = ['debug_toolbar.middleware.DebugToolbarMiddleware']

for key in os.environ:
    if key.startswith("DJANGO_"):
        var_name = re.sub('DJANGO_', '', key)
        globals()[var_name] = os.environ[key]
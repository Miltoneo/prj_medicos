"""
Django settings for prj_medicos project.
...
"""

from pathlib import Path
import environ
import os

# Adiciona a leitura da versão

from core.version import get_version
APP_VERSION = get_version(force_file=True)

#------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, True)
)
DEBUG = env('DEBUG')


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / 'templates'
STATIC_ROOT = BASE_DIR / 'static'

SECRET_KEY = 'django-insecure-ngjj!z$$f^h-0-d(05*hw(r6^jx_7a0hp_nbk^xl_x&b7!8cy+'
#DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'www.onkoto.com.br', 'onkoto.com.br','[::1]', '*'] 

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Adicionado para suporte a filtros humanize
    'medicos.apps.MilenioConfig',

    "django_bootstrap5",
    'mathfilters',
    'django_adsense_injector',
    'django.contrib.sitemaps',
    'django_extensions', 
    'django_select2',
    'jquery', 
    'crispy_forms',
    'crispy_bootstrap5',
    'django_tables2',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # SaaS Multi-tenant Middleware (reabilitado)
    'medicos.middleware.tenant_middleware.TenantMiddleware',
    'medicos.middleware.tenant_middleware.LicenseValidationMiddleware',
    'medicos.middleware.tenant_middleware.UserLimitMiddleware',
]

ROOT_URLCONF = 'prj_medicos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Não inclui a pasta raiz 'templates', busca apenas nas pastas dos apps
        'APP_DIRS': True,  # Busca automática em templates/ de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'prj_medicos.wsgi.application'

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

DATABASE_HOST       = os.environ.get('SECONDARY_DATABASE_HOST', default= env('DATABASE_HOST'))
DATABASE_NAME       = os.environ.get('SECONDARY_DATABASE_NAME', default= env('DATABASE_NAME'))
DATABASE_USER       = os.environ.get('SECONDARY_DATABASE_USER', default= env('DATABASE_USER'))
DATABASE_PASSWORD   = os.environ.get('SECONDARY_DATABASE_PASSWORD', default= env('DATABASE_PASSWORD'))
DATABASE_PORT       = os.environ.get('SECONDARY_DATABASE_PORT', default= env('DATABASE_PORT'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
        'TEST': {
            'NAME': DATABASE_NAME,  # Usa o banco real para testes (NÃO RECOMENDADO em produção)
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

TIME_ZONE = 'America/Sao_Paulo'
LANGUAGE_CODE = 'pt-br'
USE_TZ = True
USE_I18N = True
USE_L10N = True

USE_THOUSAND_SEPARATOR = True

DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d-%m-%y',)

FORMAT_MODULE_PATH = ['medicos.formats']

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/2",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

SELECT2_CACHE_BACKEND = "select2"
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]

# ------------------------------------------------------------
AUTH_USER_MODEL = 'medicos.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'medicos:login'
LOGIN_REDIRECT_URL = 'medicos:index'
LOGOUT_REDIRECT_URL = 'medicos:login'

# ----------------------------------------------#
#              smtp.onkoto.com.br ???? NAO ESTÁ AUTENTICANDO    #
# ----------------------------------------------#
# EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_USE_TLS   = True
# EMAIL_PORT      = 587
# EMAIL_HOST          = 'mail.onkoto.com.br'
# EMAIL_HOST_USER     = 'user1@onkoto.com.br'
# EMAIL_HOST_PASSWORD = '*mil031212'
# DEFAULT_FROM_EMAIL  = 'user1@mail.onkoto.com.br'
# RECIPIENT_ADDRESS   = ['None']

# ----------------------------------------------#
#              smtp.gmail.com    (teste only)   #
# ----------------------------------------------#
#https://www.geeksforgeeks.org/setup-sending-email-in-django-project/
EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS   = True
EMAIL_PORT      = 587
EMAIL_HOST         = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = 'xblz qmog fifx zqzu' # from google app register
EMAIL_HOST_USER     = 'miltoneo'
DEFAULT_FROM_EMAIL =  'suporte_tds@gmail.com'

# URL base do sistema para geração de links em e-mails
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
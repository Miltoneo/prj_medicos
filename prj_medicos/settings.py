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
    'medicos',

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
    # SaaS Multi-tenant Middleware
    'medicos.middleware.tenant_middleware.TenantMiddleware',
    'medicos.middleware.tenant_middleware.LicenseValidationMiddleware',
    'medicos.middleware.tenant_middleware.UserLimitMiddleware',
]

ROOT_URLCONF = 'prj_medicos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.app_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'prj_medicos.wsgi.application'

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SERVER_HOSTNAME     = os.environ.get('SECONDARY_SERVER_HOSTNAME', default= env('SERVER_HOSTNAME'))
DATABASE_NAME       = os.environ.get('SECONDARY_DATABASE_NAME', default= env('DATABASE_NAME'))
DATABASE_USER       = os.environ.get('SECONDARY_DATABASE_USER', default= env('DATABASE_USER'))
DATABASE_PASSWORD   = os.environ.get('SECONDARY_DATABASE_PASSWORD', default= env('DATABASE_PASSWORD'))
DATABASE_PORT       = os.environ.get('SECONDARY_DATABASE_PORT', default= env('DATABASE_PORT'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': SERVER_HOSTNAME,
        'PORT': DATABASE_PORT,
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
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ------------------------------------------------------------
AUTH_USER_MODEL = 'medicos.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'medicos:login'
LOGIN_REDIRECT_URL = 'medicos:index'
LOGOUT_REDIRECT_URL = 'medicos:login'
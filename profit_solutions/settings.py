"""
Django settings for profit_solutions project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
PKG_CONFIG_PATH = os.getenv('PKG_CONFIG_PATH')

from decouple import config 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!


SECRET_KEY = config('SECRET_KEY')
# DEBUG = config('DEBUG')
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1','solutions-flex-dev.us-west-2.elasticbeanstalk.com','http://solutions-flex-dev.us-west-2.elasticbeanstalk.com/']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'accounts_admin',
    'company',
    'customers',
    'transactions',
    'loans',
    'django.contrib.humanize',
    'reports',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'profit_solutions.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.soon_to_expire'
            ],
        },
    },
]

WSGI_APPLICATION = 'profit_solutions.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'profit_solutions',
        'USER': 'postgres',
        'PASSWORD': 'People',
        'HOST': 'localhost',
        # 'HOST': 'database-2.cxwm64gcozpx.us-west-2.rds.amazonaws.com',  # Or your database host
        'PORT': '5432',           # Leave empty for the default PostgreSQL port (5432)
    }
}




# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('NAME'),
#         'USER': config('USER'),
#         'PASSWORD': config('PASSWORD'),
#         'HOST': 'localhost',
#         'PORT': '5432',          # Leave empty for the default PostgreSQL port (5432)
#     }
# }

AUTH_USER_MODEL = 'accounts.User'
# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos'  # Set to your local timezone
USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/



# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR /'static'
STATICFILES_DIRS = [
    'profit_solutions/static',
    # os.path.join(BASE_DIR, 'your_app/static'),
]

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR /'media'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

USE_L10N = True
L10N = {
    'currency_symbol': 'N',  # Set your desired currency symbol here
}
config('USER')

# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ADMIN_MEDIA_PREFIX = '/static/admin'



AUTHENTICATION_BACKENDS = [
    'company.backends.LicenseExpirationBackend', 
    'django.contrib.auth.backends.ModelBackend',
]
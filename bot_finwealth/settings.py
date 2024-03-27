"""
Django settings for bot_finwealth project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from .jazzmin import *
from datetime import timedelta, datetime as dt
from dotenv import load_dotenv


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tr7*9sss-=8lug67x*9pktqewkwp+9(+p9*&de)zc-zczcvg3e'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CSRF_TRUSTED_ORIGINS = ['https://finwealth.vn']

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django_crontab',
    'jazzmin',
    'rest_framework',
    'debug_toolbar',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'telegram_bot',
    'data_source',
    'manage_bots',
    'signal_bots',
    'bot_user',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware', 
]

ROOT_URLCONF = 'bot_finwealth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'bot_finwealth.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES_LIST = [
    {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }

    },
]
DATABASES = DATABASES_LIST[0]


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Ho_Chi_Minh'

USE_I18N = True

USE_L10N = False

USE_TZ = False

DATE_FORMAT = ( ( 'd-m-Y' ))
DATE_INPUT_FORMATS = ( ('%d-%m-%Y'),)
DATETIME_FORMAT = (( 'd-m-Y H:i' ))
DATETIME_INPUT_FORMATS = (('%d-%m-%Y %H:%i'),)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = Path.joinpath(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = Path.joinpath(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
JAZZMIN_SETTINGS = JAZZMIN_SETTINGS
JAZZMIN_UI_TWEAKS = JAZZMIN_UI_TWEAKS

CRONTAB_TIMEZONE = 'Asia/Ho_Chi_Minh'

# Ví dụ cấu hình cho việc sao lưu vào thư mục 'backups/'
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'

DBBACKUP_CLEANUP_KEEP = True
DBBACKUP_CLEANUP_KEEP_NUMBER = 3  # Số lượng bản sao lưu giữ lại
DBBACKUP_STORAGE_OPTIONS = {
    'location': '/root/ecotrading/backup/', 
}



def custom_backup_filename(databasename, servername, extension,datetime, content_type):
    formatted_datetime = dt.now().strftime('%Y-%m-%d') 
    return f"{formatted_datetime}.{extension}"

DBBACKUP_FILENAME_TEMPLATE = custom_backup_filename

FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 10  # 10MB
# Kích thước tệp được phép tải lên (1MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 10  # 10MB

CRONJOBS = [
    # ('0 0 * * *', 'ecotrading.schedule.schedule_morning'),# chạy lúc 7 giờ sáng
    # ('30 4 * * 1-5', 'ecotrading.schedule.schedule_mid_trading_date'),# chạy lúc 11h30 sáng
    ('30 8 * * 1-5', 'signal_bots.filter.filter_stock_daily'),# chạy lúc 15h trưa
    ('40 9 * * 1-5', 'signal_bots.models.stock_pitch_valuation'), # Chạy lúc 15:40 từ thứ 2 đến thứ 6
    # ('30 15 * * 1-5', 'portfolio.models.get_all_info_stock_price'), # Chạy lúc 21h từ thứ 2 đến thứ 6
    ('45 16 * * *', 'bot_user.models.cal_used_point'),
    ('55 16 * * *', 'data_source.function.delete_file_pdf'),
]

    
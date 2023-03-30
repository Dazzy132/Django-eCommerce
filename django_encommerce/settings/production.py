from .base import *

DEBUG = os.getenv('DEBUG')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(',')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME':  os.getenv('DB_NAME'),
        'USER':  os.getenv('DB_USER'),
        'PASSWORD':  os.getenv('DB_PASSWORD'),
        'HOST':  os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT')
    }
}

STRIPE_PUBLIC_KEY = os.getenv('STRIPE_LIVE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_LIVE_SECRET_KEY')
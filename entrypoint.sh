#!/bin/sh
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input
gunicorn --bind 0:8000 django_encommerce.wsgi:application

exec "$@"
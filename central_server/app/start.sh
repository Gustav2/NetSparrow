#!/bin/sh

python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations website
python manage.py migrate website
python manage.py collectstatic --noinput

exec gunicorn --bind 0.0.0.0:8000 --workers 3 myproject.wsgi:application
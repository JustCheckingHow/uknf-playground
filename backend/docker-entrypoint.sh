#!/bin/sh
set -e

python manage.py makemigrations --merge --noinput
python manage.py migrate --noinput

exec "$@"

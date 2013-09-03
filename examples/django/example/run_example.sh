#!/bin/sh

# Activate virtual environment.
. ../../../venv/bin/activate

# Start the django development server.
python manage.py runserver 8080
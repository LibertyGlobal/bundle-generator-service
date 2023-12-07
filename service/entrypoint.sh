#!/usr/bin/env bash

echo "Activating Poetry virtualenv"
source $(poetry env info --path)/bin/activate
echo "Activated"

echo "Starting Gunicorn with Flask application"
PYTHONPATH=$(dirname `pwd`):$PYTHONPATH gunicorn --bind 0.0.0.0:8081 app:app --daemon
echo "Gunicorn started"

echo "Starting Worker"
PYTHONPATH=$(dirname `pwd`):$PYTHONPATH python3 ./worker.py

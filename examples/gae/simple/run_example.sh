#!/bin/sh

# Activate virtual environment.
. ../../../venv/bin/activate

# Run GAE dev server.
python ../../../venv/bin/google_appengine/dev_appserver.py --port 8080 .
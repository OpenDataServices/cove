#!/bin/bash

if [ ! -z "$PROCESS_DATA" ]; then
    /usr/local/bin/process.sh
    exit $?
fi

/usr/local/bin/update.sh
cd /opt/cove
export DJANGO_SETTINGS_MODULE=cove_iati.settings
python3 manage.py migrate
python3 manage.py compilemessages
python3 manage.py runserver

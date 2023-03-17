#!/bin/bash

set -e

############################# Get vars

# To increase this, you also need to set the Dokku config
#   dokku nginx:set APPNAME proxy-read-timeout 120s
#   dokku proxy:build-config APPNAME
# If you are using Dokkusd to deploy, make sure GitHub actions also sets
# DOKKUSD_NGINX_PROXY_READ_TIMEOUT and Dokkusd will do that for you.
set APP_TIMEOUT_SECONDS="${APP_TIMEOUT_SECONDS:=60}"

# To increase this, you also need to set the Dokku config
#   dokku nginx:set APPNAME client-max-body-size 50m
# If you are using Dokkusd to deploy, make sure GitHub actions also sets
# DOKKUSD_NGINX_CLIENT_MAX_BODY_SIZE and Dokkusd will do that for you.
set APP_UPLOAD_MAXIMUM_MEGABYTES="${APP_UPLOAD_MAXIMUM_MEGABYTES:=1}"

############################# Set up config files
cp /app/docker/nginx.conf /etc/nginx/sites-available/default

sed -i 's/APP_TIMEOUT_SECONDS/'$APP_TIMEOUT_SECONDS'/g' /etc/nginx/sites-available/default
sed -i 's/APP_UPLOAD_MAXIMUM_MEGABYTES/'$APP_UPLOAD_MAXIMUM_MEGABYTES'/g' /etc/nginx/sites-available/default

############################# Start Services
/etc/init.d/nginx start
cd /app
gunicorn --bind 0.0.0.0:8000 --timeout $APP_TIMEOUT_SECONDS cove_iati.wsgi:application

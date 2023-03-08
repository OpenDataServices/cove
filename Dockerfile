FROM python:3.11-bullseye

# Setup

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

RUN apt-get update
RUN apt-get --assume-yes install gettext nginx

# Git

RUN git config --global --add safe.directory /app

# Python

# Build our own copy of lxml using Ubuntu's libxml2/libxslt
# (don't use the prebuilt wheel)
# https://opendataservices.plan.io/issues/36790
RUN apt install libxml2-dev libxslt-dev
RUN pip install --no-binary lxml -r requirements.txt

RUN python manage.py collectstatic --noinput
RUN python manage.py compilemessages

# Webserver

COPY docker/nginx.conf /etc/nginx/sites-available/default

# Run

EXPOSE 80

CMD /bin/bash -c "/etc/init.d/nginx start && gunicorn --bind 0.0.0.0:8000 --timeout 900 cove_iati.wsgi:application"

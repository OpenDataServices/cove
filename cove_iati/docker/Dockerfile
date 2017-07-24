FROM python:3
MAINTAINER tobias@neontribe.co.uk

WORKDIR /opt/cove
ENV SECRET_KEY=somesecretkey

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get -y install git vim htop gettext && \
    git clone https://github.com/OpenDataServices/cove.git /opt/cove && \
    git fetch && \
    pip3 install cython && \
    pip3 install -r requirements_iati.txt && \
    python manage.py migrate && \
    python manage.py compilemessages && \
    mkdir -p media


RUN apt install coreutils
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8008
EXPOSE 8000

COPY startup.sh /usr/local/bin/startup.sh
COPY update.sh /usr/local/bin/update.sh
COPY process.sh /usr/local/bin/process.sh

ENV DJANGO_SETTINGS_MODULE=cove_iati.settings

# ENTRYPOINT ["/usr/local/bin/startup.sh"]
ENTRYPOINT ["/bin/bash"]

# vim: set filetype=dockerfile expandtab tabstop=3 shiftwidth=2 autoindent smartindent:

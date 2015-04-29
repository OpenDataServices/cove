Cove - COnvert Validate & Explore
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://travis-ci.org/OpenDataServices/cove.svg?branch=master
    :target: https://travis-ci.org/OpenDataServices/cove

.. image:: https://requires.io/github/OpenDataServices/cove/requirements.svg?branch=master
     :target: https://requires.io/github/OpenDataServices/cove/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://coveralls.io/repos/OpenDataServices/cove/badge.png?branch=master
    :target: https://coveralls.io/r/OpenDataServices/cove?branch=master

.. image:: https://img.shields.io/badge/license-AGPLv3-blue.svg
    :target: https://github.com/OpenDataServices/cove/blob/master/AGPLv3.txt

Introduction
============

This application is currently in a pre-alpha state.

Requirements
============
This application is built using Django and python 3

Installation
============
Steps to installation:

* Clone the repository
* Change into the cloned repository
* Create a virtual environment (note this application uses python3)
* Activate the virtual environment
* Install dependencies
* Set up the database (sqlite3)
* Compile the translations
* Run the development server

.. code:: bash

    git clone https://github.com/OpenDataServices/cove.git
    cd cove
    virtualenv .ve --python=/usr/bin/python3
    source .ve/bin/activate
    pip install -r requirements_dev.txt
    python manage.py migrate
    python manage.py compilemessages
    python manage.py runserver

Follow the instructions in your terminal to open the aplication in your browser.

Run tests
=========

.. code:: bash

    py.test

To genreate a coverage report (in the htmlcov directory):

.. code:: bash

    py.test --cov cove --cov-report html

Translations
============

For more information about Django's translation framework, see https://docs.djangoproject.com/en/1.8/topics/i18n/translation/

If you add new text to the interface, ensure to wrap it in the relevant gettext blocks/functions, and then regnerate the .po files in the locale folder:

.. code:: bash

    python manage.py makemessages

To check that all new text is written so that it is able to be translated you could install and run `django-template-i18n-lint`

.. code:: bash

    pip install django-template-i18n-lint
    django-template-i18n-lint cove

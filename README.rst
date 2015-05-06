CoVE - Convert Validate & Explore
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

The W3C `Data on the Web Best Practices <http://www.w3.org/TR/dwbp/>`_ recommend making open data available in a range of formats to meet the needs of different users. Developers may want JSON, researchers might prefer a spreadsheet format.

CoVE manages the process of converting between JSON, Excel and CSV formats for structured data. 

CoVE presents key validation information during the process, and can be configured to display information about the contents of a data file, so that it can be easily inspected.

Supported formats
+++++++++++++++++

CoVE currently supports conversion from: 

 * JSON to multi-tabbed Excel files 
 * Excel to JSON (it uses the `flatten-tool <(https://github.com/OpenDataServices/flatten-tool>`_ for conversion) 
 
If a JSON schema is supplied, CoVE can use either field names, or user-friendly column titles. 

Exploration views need to be developed, customised to the type of data being converted.

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

To generate a coverage report (in the htmlcov directory):

.. code:: bash

    py.test --cov cove --cov-report html

The tests include functional tests (actually interacting with the website in selenium). These can also be run against a deployed copy of the website:

.. code:: bash

    CUSTOM_SERVER_URL=http://dev.cove.opendataservices.coop py.test fts 

Translations
============

| We use Django's transaltion framework to provide this application in different languages.
| We have used Google Translate to perform initial translations from English, but expect those translations to be worked on by humans over time.

Translations for Translators
++++++++++++++++++++++++++++
Translators can provide translations for this application by editing the django.po file for a particular language.
These files are found in the `locale` directory

Translations for Developers
+++++++++++++++++++++++++++
For more information about Django's translation framework, see https://docs.djangoproject.com/en/1.8/topics/i18n/translation/

If you add new text to the interface, ensure to wrap it in the relevant gettext blocks/functions, and then regnerate the .po files in the locale folder:

.. code:: bash

    python manage.py makemessages

To check that all new text is written so that it is able to be translated you could install and run `django-template-i18n-lint`

.. code:: bash

    pip install django-template-i18n-lint
    django-template-i18n-lint cove

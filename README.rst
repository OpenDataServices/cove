Cove - COnvert Validate & Explore
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Translations
============

For more information about Django's translation framework, see https://docs.djangoproject.com/en/1.8/topics/i18n/translation/

If you add new text to the interface, ensure to wrap it in the relevant gettext blocks/functions, and then regnerate the .po files in the locale folder:

.. code:: bash

    python manage.py makemessages

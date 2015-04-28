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
* Run the development server

.. code:: bash

    git clone ...
    cd <hjekkjr>
    virtualenv pyenv --python=/usr/bin/python3
    source pyenv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

Follow the instructions in your terminal to open the aplication in your browser.

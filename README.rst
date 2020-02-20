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

Development work on CoVE by Open Data Services is carried out in sprints. The issues for each sprint can be found at https://github.com/OpenDataServices/cove/projects . Other work is carried out from time to time, and contributions from the community are welcome. Outstanding issues for CoVE can be found at https://github.com/OpenDataServices/cove/issues . Please report any bugs!

Introduction
============

CoVE is an web application to Convert, Validate and Explore data following certain open data standards - currently 360Giving and the Open Contracting Data standard. http://cove.opendataservices.coop

Why convert data?
+++++++++++++++++

The W3C `Data on the Web Best Practices <http://www.w3.org/TR/dwbp/>`_ recommend making open data available in a range of formats to meet the needs of different users. Developers may want JSON, researchers might prefer a spreadsheet format.

CoVE manages the process of converting between JSON, Excel and CSV formats for structured data.

Validate and Explore
++++++++++++++++++++

CoVE presents key validation information during the process, and can be configured to display information about the contents of a data file, so that it can be easily inspected.

Supported formats
+++++++++++++++++

CoVE currently supports conversion from:

* JSON to multi-tabbed Excel files
* Excel to JSON (it uses the `flatten-tool <https://github.com/OpenDataServices/flatten-tool>`_ for conversion)

If a JSON schema is supplied, CoVE can use either field names or user-friendly column titles.

User Flows
==========

Overviews of how users flow through the application are maintained at https://docs.google.com/drawings/d/1pVbEu6dJaVk8t3NctjYuE5irsqltc9Th0gVQ_zeJyFA/edit and https://docs.google.com/drawings/d/1wFH4lZlBZWso7Tj_g7CyTF3YaFfnly59sVufpztmEg8/edit

Putting code live
=================

There are live instances at:
https://dataquality.threesixtygiving.org/
http://standard.open-contracting.org/review/
https://iati.cove.opendataservices.coop/

Code is deployed to live when it is merged into the master branch. (Instructions on how to do this at https://cove.readthedocs.io/en/latest/deployment/).

Feature requests, bugs, questions and answers etc are all handled via GitHub.

Requirements
============
This application is built using Django and Python 3.5

Installation
============
Steps to installation:

* Clone the repository
* Change into the cloned repository
* Create a virtual environment (note this application uses python3)
* Activate the virtual environment
* Install dependencies
* Set up the database (sqlite3) (you need to pass the django settings for the module (ie. 360, iati) you want to run)
* Compile the translations
* Run the development server

.. code:: bash

    git clone https://github.com/OpenDataServices/cove.git
    cd cove
    python3 -m venv .ve
    source .ve/bin/activate
    pip install -r requirements_dev.txt
    DJANGO_SETTINGS_MODULE={cove_MODULENAME}.settings python manage.py migrate
    python manage.py compilemessages

Then, for 360Giving run:

.. code:: bash

    DJANGO_SETTINGS_MODULE=cove_360.settings python manage.py runserver

Follow the instructions in your terminal to open the application in your browser.

Extra installation steps for IATI
+++++++++++++++++++++++++++++++++

The following steps are for Ubuntu but equivalent packages are available for other distros.

.. code:: bash

   sudo apt-get install build-essential libxml2-dev libxslt1-dev python3-dev
   pip install -r requirements_iati.txt

Then run the development server:

.. code:: bash

    DJANGO_SETTINGS_MODULE=cove_iati.settings python manage.py runserver


Deployment
==========

See https://cove.readthedocs.io/en/latest/deployment/

Run tests
=========

.. code:: bash

   ./run_tests.sh

To run functional tests with a different browser:

.. code:: bash

   BROWSER=Chrome ./run_tests.sh

See http://selenium-python.readthedocs.io/api.html for browser options.

To generate a coverage report (in the htmlcov directory):

.. code:: bash

    py.test --cov cove --cov-report html

The tests include functional tests (actually interacting with the website in selenium). These can also be run against a deployed copy of the website:

.. code:: bash

    CUSTOM_SERVER_URL=http://dev.cove.opendataservices.coop py.test fts

We also use flake8 to test code quality, see https://github.com/OpenDataServices/developer-docs/blob/master/tests.md#flake8

The development requirements include xdist to allow running tests in parallel:

.. code:: bash

    py.test -n2

Translations
============

| We use Django's translation framework to provide this application in different languages.
| We have used Google Translate to perform initial translations from English, but expect those translations to be worked on by humans over time.

Translations for Translators
++++++++++++++++++++++++++++
Translators can provide translations for this application by becomming a collaborator on Transifex https://www.transifex.com/OpenDataServices/cove

Translations for Developers
+++++++++++++++++++++++++++

For more information about Django's translation framework, see https://docs.djangoproject.com/en/1.8/topics/i18n/translation/

If you add new text to the interface, ensure to wrap it in the relevant gettext blocks/functions.

In order to generate messages and post them on Transifex:

First check the `Transifex lock <https://opendataservices.plan.io/projects/co-op/wiki/CoVE_Transifex_lock>`_, because only one branch can be translated on Transifex at a time.

Make sure you are set up as a maintainer in Transifex. Only maintainers are allowed to update the source file.

Install `gettext <https://www.gnu.org/software/gettext/>`_ library. (The following step is for Ubuntu but equivalent packages are available for other distros.)

.. code:: bash

    sudo apt-get install gettext

Then:

.. code:: bash

    python manage.py makemessages -l en
    tx push -s

In order to fetch messages from transifex:

.. code:: bash

    tx pull -a

In order to compile them:

.. code:: bash

    python manage.py compilemessages

Keep the makemessages and pull messages steps in thier own commits seperate from the text changes.

To check that all new text is written so that it is able to be translated you could install and run `django-template-i18n-lint`

.. code:: bash

    pip install django-template-i18n-lint
    django-template-i18n-lint cove

Adding and updating requirements
================================

Add a new requirements to ``requirements.in`` or ``requirements_dev.in`` depending on whether it is just a development requirement or not.


Then, run ``./update_requirements --new-only`` this will populate ``requirements.txt`` and/or ``requirements_dev.txt`` with pinned versions of the new requirement and it's dependencies.

WARNING: The ``./update_requirements`` script will delete and recreate your current ``.ve`` directory.

``./update_requirements`` without any flags will update all pinned requirements to the latest version. Generally we don't want to do this at the same time as adding a new dependency, to make testing any problems easier.


Command Line Interface
======================

**IATI**

.. code:: bash

    ./iati-cli --options file-name

``file-name`` can be a XML or an Excel/CSV file.

Options:

``--output-dir -o``  Directory where the output will be created, defaults to the name of the file.

``--exclude-file -e``  Do not include the file in the output directory.

``--delete -d`` Delete the output directory if it already exists.

``--orgids -i`` Run org-ids rule check for IATI identifier prefixes.

``--openag -a`` Run ruleset checks for IATI OpenAg data.


If the file is in spreadsheet format, the output directory will contain a *unflattened.xml* file converted from Excel or CSV to XML format

**OpenaAg** rulesets check that the data contains the XML elements ``<opeang:tag>`` and ``<location>``, and that they include the right attributes expected for OpenAg data. Please read `OpenAg ruleset feature files <cove_iati/rulesets/iati_openag_ruleset/>`_ (written in `Gerkhin <https://github.com/cucumber/cucumber/wiki/Gherkin/>`_ style) for more information.

**Org-ids** rulesets check that all organisation identifiers are prefixed with a registered `org-ids <http://org-id.guide>`_ prefix. Please read `Org-ids ruleset feature file <cove_iati/rulesets/iati_orgids_ruleset/>`_ for more information


**Non Embedded Codelists** 

Non embedded codelists need to be periodically downloaded and committed to this repo.  To do this run in the virtualenv:

.. code:: bash

   python get_iati_non_embedded_codelists.py 




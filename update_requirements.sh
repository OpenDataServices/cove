#!/bin/bash
# This follows broadly the approach from
# http://www.kennethreitz.org/essays/a-better-pip-workflow but with the
# addition of requirements_dev
rm -rf .ve
virtualenv --python=python3 .ve
source .ve/bin/activate
pip install --upgrade -r requirements.in
pip freeze -r requirements.in > requirements.txt
pip install --upgrade -r requirements_dev.in
pip freeze -r requirements_dev.in > requirements_dev.txt
# Put comments back on the same line (mostly for requires.io's benefit)
sed -ie '$!N;s/\n#^^/ #/;P;D' requirements*txt

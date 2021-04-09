#!/bin/bash
# This follows broadly the approach from
# http://www.kennethreitz.org/essays/a-better-pip-workflow but with the
# addition of requirements_dev

# Delete and recreate a virtualenv to ensure that we don't have any extra
# packages installed in it
rm -rf .ve
python3.6 -m venv .ve
source .ve/bin/activate

pip install --upgrade pip

if [[ "$1" == "--new-only" ]]; then
    # If --new-only is supplied then we install the current versions of
    # packages into the virtualenv, so that the only change will be any new
    # packages and their dependencies.
    pip install -r requirements.txt
    dashupgrade=""
else
    dashupgrade="--upgrade"
fi
pip install $dashupgrade -r requirements.in
pip freeze -r requirements.in > requirements.txt

# Same again for requirements_dev
if [[ "$1" == "--new-only" ]]; then
    pip install -r requirements_dev.txt
fi
pip install $dashupgrade -r requirements_dev.in
cat requirements.in requirements_dev.in > requirements_combined_tmp.in
pip freeze -r requirements_combined_tmp.in > requirements_dev.txt
rm requirements_combined_tmp.in

# Put comments back on the same line (mostly for requires.io's benefit)
sed -i '$!N;s/\n#\^\^/ #/;P;D' requirements.txt requirements_dev.txt
sed -i 's/^-r.*//' requirements.txt requirements_dev.txt
sed -i 's/pkg-resources==0.0.0//' requirements.txt requirements_dev.txt

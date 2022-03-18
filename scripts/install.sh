#!/bin/bash

./scripts/clean.sh

if [ -x "$(which python)" ]; then
    virtualenv --clear --no-site-packages -p python py2

    ./py2/bin/pip install wheel
    ./py2/bin/pip install coverage
    ./py2/bin/pip install -e .[test]
fi
if [ -x "$(which python3)" ]; then
    virtualenv --clear --no-site-packages -p python3 py3

    ./py3/bin/pip install wheel
    ./py3/bin/pip install coverage
    ./py3/bin/pip install -e .[test]
fi

#!/bin/sh

./$1/bin/coverage run --source=src/node/ext/ugm -m node.ext.ugm.tests.__init__
./$1/bin/coverage report
./$1/bin/coverage html

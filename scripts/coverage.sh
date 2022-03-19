#!/bin/bash

function run_coverage {
    local target=$1

    if [ -e "$target" ]; then
        ./$target/bin/coverage run \
            --source=src/node/ext/ugm \
            -m node.ext.ugm.tests.__init__
        ./$target/bin/coverage report
    else
        echo "Target $target not found."
    fi
}

run_coverage py2
run_coverage py3
run_coverage pypy3

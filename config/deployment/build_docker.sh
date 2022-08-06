#!/bin/bash
#
# Script to build a Docker image.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

# Abort on error.
set -e;

docker build -f $1 --force-rm --no-cache -t log2timeline/plaso . ;

docker run log2timeline/plaso log2timeline.py --version;

exit ${EXIT_SUCCESS};


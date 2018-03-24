#!/bin/bash
#
# Script to run the end-to-end tests on a Greendale image

SOURCES_DIRECTORY="/media/greendale_images";
RESULTS_DIRECTORY="plaso-out";

sh ./config/linux/gift_ppa_install.sh include-test

mkdir -p ${RESULTS_DIRECTORY}

git log -1 --pretty=oneline > ${RESULTS_DIRECTORY}/COMMIT

PYTHONPATH=. python ./tests/end-to-end.py --config ${JOB_NAME}.ini --sources-directory ${SOURCES_DIRECTORY} --tools-directory ./tools --results-directory ${RESULTS_DIRECTORY} --references-directory ${SOURCES_DIRECTORY}


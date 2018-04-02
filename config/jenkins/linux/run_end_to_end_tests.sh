#!/bin/bash
#
# Script to run end-to-end tests on Ubuntu Jenkins instance.

CONFIGURATION_FILE="${JOB_NAME}.ini";

SOURCES_DIRECTORY="/media/greendale_images";
REFERENCES_DIRECTORY="/media/greendale_images";
RESULTS_DIRECTORY="plaso-out";

./config/linux/gift_ppa_install.sh include-test;

mkdir -p ${RESULTS_DIRECTORY};

if ! test -f ${CONFIGURATION_FILE};
then
	CONFIGURATION_FILE="config/jenkins/greendale/${CONFIGURATION_FILE}";
fi

PYTHONPATH=. ./tests/end-to-end.py --config ${CONFIGURATION_FILE} --sources-directory ${SOURCES_DIRECTORY} --tools-directory ./tools --results-directory ${RESULTS_DIRECTORY} --references-directory ${REFERENCES_DIRECTORY};

#!/bin/bash
#
# Script to run end-to-end tests on Ubuntu Jenkins instance.

CONFIGURATION_FILE="${JOB_NAME}.ini";

SOURCES_DIRECTORY="/media/greendale_images";
REFERENCES_DIRECTORY="/media/greendale_images";
RESULTS_DIRECTORY="plaso-out";

LOGGING_OPTIONS="--debug --log-file=${RESULTS_DIRECTORY}/log2timeline.log.gz";
PROFILING_OPTIONS="--profilers=all --profiling_directory=${RESULTS_DIRECTORY}"

./config/linux/gift_ppa_install.sh include-test;

mkdir -p ${RESULTS_DIRECTORY};

# Remove old profiling options set in the configuration. 
sed "s/^\(extract_options=.*\) --profile .*$/\1/" -i ${CONFIGURATION_FILE};

# Add log2timeline.py logging and profiling options.
sed "s/^\(extract_options=.*\)$/\1 ${LOGGING_OPTIONS} ${PROFILING_OPTIONS}/" -i ${CONFIGURATION_FILE};

PYTHONPATH=. ./tests/end-to-end.py --config ${CONFIGURATION_FILE} --sources-directory ${SOURCES_DIRECTORY} --tools-directory ./tools --results-directory ${RESULTS_DIRECTORY} --references-directory ${REFERENCES_DIRECTORY};

#!/bin/bash
#
# Script to run end-to-end tests on Ubuntu Jenkins instance.

# Fail on error.
set -e

CONFIGURATION=$1;

CONFIGURATION_FILE="${CONFIGURATION}.ini";

SOURCES_DIRECTORY="/media/greendale_images";
REFERENCES_DIRECTORY="/media/greendale_images";

RESULTS_DIRECTORY="plaso-out";

./config/linux/gift_ppa_install.sh include-test;

# Change path to test this script on Travis-CI.
if test ${CONFIGURATION} = 'travis';
then
	SOURCES_DIRECTORY="test_data";
	REFERENCES_DIRECTORY="test_data/end_to_end";
	CONFIGURATION_FILE="config/jenkins/${CONFIGURATION_FILE}";
fi

mkdir -p ${RESULTS_DIRECTORY} ${RESULTS_DIRECTORY}/profiling;

if ! test -f ${CONFIGURATION_FILE};
then
	CONFIGURATION_FILE="config/jenkins/greendale/${CONFIGURATION_FILE}";
fi
if ! test -f ${CONFIGURATION_FILE};
then
	CONFIGURATION_FILE="config/jenkins/sans/${CONFIGURATION_FILE}";
fi

PYTHONPATH=. ./utils/check_dependencies.py

# Start the end-to-end tests in the background so we can capture the PID of
# the process while the script is running.
PYTHONPATH=. ./tests/end-to-end.py --config ${CONFIGURATION_FILE} --sources-directory ${SOURCES_DIRECTORY} --tools-directory ./tools --results-directory ${RESULTS_DIRECTORY} --references-directory ${REFERENCES_DIRECTORY} &

PID_COMMAND=$!;

echo "End-to-end tests started (PID: ${PID_COMMAND})";

wait ${PID_COMMAND};

RESULT=$?;

# On Travis-CI print the stdout and stderr output to troubleshoot potential issues.
if test ${CONFIGURATION} = 'travis';
then
	for FILE in `find ${RESULTS_DIRECTORY} -name \*.out -type f`;
	do
		echo "stdout file: ${FILE}";
		cat ${FILE};
		echo "";
	done

	for FILE in `find ${RESULTS_DIRECTORY} -name \*.err -type f`;
	do
		echo "stderr file: ${FILE}";
		cat ${FILE};
		echo "";
	done
fi

exit ${RESULT};

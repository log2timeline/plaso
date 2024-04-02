#!/bin/bash
#
# Script to run end-to-end tests on a Linux Jenkins instance with Docker.

# Fail on error.
set -e

CONFIGURATION_NAME=$1;

CONFIGURATION_DIRECTORY="${PWD}/config/jenkins/greendale";

if ! test -f "${CONFIGURATION_DIRECTORY}/${CONFIGURATION_NAME}.ini";
then
	CONFIGURATION_DIRECTORY="${PWD}/config/jenkins/sans";
fi
if ! test -f "${CONFIGURATION_DIRECTORY}/${CONFIGURATION_NAME}.ini";
then
	CONFIGURATION_DIRECTORY="${PWD}/config/jenkins/other";
fi

SOURCES_DIRECTORY="/media/greendale_images";

cd config/end_to_end;

RESULTS_DIRECTORY="${PWD}/plaso-out";

mkdir -p "${RESULTS_DIRECTORY}/profiling";

# Build the extract_and_output end-to-end test Docker image.
docker build -f extract_and_output.Dockerfile --force-rm --no-cache -t log2timeline/plaso . ;

docker run log2timeline/plaso ./utils/check_dependencies.py;

docker run -v "${CONFIGURATION_DIRECTORY}:/config:z" -v "${RESULTS_DIRECTORY}:/home/test/plaso/plaso-out:z" -v "${SOURCES_DIRECTORY}:/sources:z" log2timeline/plaso /bin/bash -c "./tests/end-to-end.py --config /config/${CONFIGURATION_NAME}.ini --references-directory test_data/end_to_end --results-directory /home/test/plaso/plaso-out --sources-directory /sources --scripts-directory plaso/scripts"

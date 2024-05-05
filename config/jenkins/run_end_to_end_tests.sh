#!/bin/bash
#
# Script to run end-to-end tests on an Ubuntu Jenkins instance with Docker.

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

# Build the end-to-end test Docker image.
docker build -f extract_and_output.Dockerfile --force-rm --no-cache -t log2timeline/plaso . ;

docker run log2timeline/plaso ./utils/check_dependencies.py;

COMMAND="./tests/end-to-end.py --config /config/${CONFIGURATION_NAME}.ini --references-directory test_data/end_to_end --results-directory /home/test/plaso/plaso-out --sources-directory /sources --scripts-directory plaso/scripts";

if test ${CONFIGURATION_NAME} = "psort-studentpc1-nsrlsvr";
then
	DOCKER_NETWORK="--network=nsrlsvr-network";

elif test ${CONFIGURATION_NAME} = "output_opensearch" || test ${CONFIGURATION_NAME} = "output_opensearch_ts";
then
	DOCKER_NETWORK="--network=opensearch-network";

elif test ${CONFIGURATION_NAME} = "studentpc1-redis";
then
	DOCKER_NETWORK="--network=redis-network";
fi

docker run --name=plaso ${DOCKER_NETWORK} -v "${CONFIGURATION_DIRECTORY}:/config:z" -v "${RESULTS_DIRECTORY}:/home/test/plaso/plaso-out:z" -v "${SOURCES_DIRECTORY}:/sources:z" log2timeline/plaso /bin/bash -c "${COMMAND}"

#!/bin/bash
#
# Script to build a Docker image.

EXIT_FAILURE=1
EXIT_SUCCESS=0

PPA_TRACK="stable"

# Abort on error.
set -e

pushd config/docker

LOGFILE="dockerbuild.$$"

docker build \
	--build-arg PPA_TRACK=${PPA_TRACK} \
	--no-cache \
	--force-rm \
	-t log2timeline/plaso \
	. 2>&1 | tee ${LOGFILE}

IDENTIFIER=$( grep -e ' writing image ' ${LOGFILE} | sed 's/^.* writing image //;s/ done$//' )

docker run \
	log2timeline/plaso \
	log2timeline --version 2>&1 | tee ${LOGFILE}

VERSION=$( grep -e '^plaso - log2timeline version ' ${LOGFILE} | sed 's/^plaso - log2timeline version //' )

docker tag ${IDENTIFIER} log2timeline/plaso:${VERSION}

if [ "${PPA_TRACK}" = "stable" ]; then
	docker tag ${IDENTIFIER} log2timeline/plaso:latest
else
	docker tag ${IDENTIFIER} log2timeline/plaso:${PPA_TRACK}
fi

rm -f ${LOGFILE}

popd

echo "Docker build successful."

exit ${EXIT_SUCCESS}


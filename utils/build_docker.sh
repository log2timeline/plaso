#!/bin/bash
#
# Script to build a Docker image.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

LOGFILE="dockerbuild.$$";

# Abort on error.
set -e;

cd config/docker;

docker build --no-cache --force-rm -t log2timeline/plaso . 2>&1 | tee ${LOGFILE};

IDENTIFIER=$( grep -e '^Successfully built ' ${LOGFILE} | sed 's/^Successfully built //' );

docker run log2timeline/plaso log2timeline --version 2>&1 | tee ${LOGFILE};

VERSION=$( grep -e '^plaso - log2timeline version ' ${LOGFILE} | sed 's/^plaso - log2timeline version //' );

docker tag ${IDENTIFIER} log2timeline/plaso:${VERSION}
docker tag ${IDENTIFIER} log2timeline/plaso:latest

rm -f ${LOGFILE};

echo "Docker build successful."

exit ${EXIT_SUCCESS};


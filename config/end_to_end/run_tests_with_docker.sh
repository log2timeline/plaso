#!/bin/bash
#
# Script to run Plaso end-to-end tests with Docker.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

if [[ $# -ne 3 ]];
then
	echo "Usage: run_tests_with_docker.sh CONFIGURATIONS SOURCES RESULTS";
	echo "";
	echo "Arguments";
	echo "    CONFIGURATIONS: path of the directory that contains the test configurations.";
	echo "    SOURCES: path of the directory that contains the test (source) data.";
	echo "    RESULTS: path of the directory to write test results to.";
	echo "";

	exit ${EXIT_FAILURE};
fi

TEST_CONFIGURATIONS=$1;
TEST_SOURCES=$2;
TEST_RESULTS=$3;

if [[ ! -d ${TEST_CONFIGURATIONS} ]];
then
	echo "Missing test configurations directory: ${TEST_CONFIGURATIONS}";

	exit ${EXIT_FAILURE};
fi

if [[ ! -d ${TEST_SOURCES} ]];
then
	echo "Missing test (source) data directory: ${TEST_SOURCES}";

	exit ${EXIT_FAILURE};
fi

if [[ ! -d ${TEST_RESULTS} ]];
then
	echo "Missing test results directory: ${TEST_RESULTS}";

	exit ${EXIT_FAILURE};
fi

# Abort on error.
set -e;

cd config/end_to_end;

# Build the extract_and_output end-to-end test Docker image.
docker build -f extract_and_output.Dockerfile --force-rm --no-cache -t log2timeline/plaso . ;

docker run log2timeline/plaso ./utils/check_dependencies.py;

for CONFIG_FILE in ${TEST_CONFIGURATIONS}/*.ini;
do
	TEST_NAME=`basename ${CONFIG_FILE} | sed 's/\.ini$//'`;
	TEST_CASE=`grep -e '^case=' ${CONFIG_FILE} | sed 's/^case=//'`;

	if [[ ${TEST_CASE} != "extract_and_output" ]] && [[ ${TEST_CASE} != "output" ]];
	then
		echo "Unsupported test case: ${TEST_CASE} for end-to-end test: ${TEST_NAME}";

		continue;
	fi
	OUTPUT_FORMAT=`grep -e '^output_format=' ${CONFIG_FILE} | sed 's/^output_format=//'`;

	# Note that output is mapped to /home/test/plaso/plaso-out to ensure files
	# created by the end-to-end.py script are stored outside the container.

	COMMAND="./tests/end-to-end.py --config /config/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /sources --tools-directory ./tools";

	# TODO: move custom test setup and teardown scripts to configuration parameter?

	if [[ ${OUTPUT_FORMAT} == "opensearch" ]] || [[ ${OUTPUT_FORMAT} == "opensearch_ts" ]];
	then
		# Install OpenSearch and give it 3 minutes to start-up before running the output end-to-end test.
		COMMAND="./config/linux/ubuntu_install_opensearch.sh && sleep 3m && ${COMMAND}";
	fi

	if [[ ${TEST_NAME} == "acserver-mounted" ]];
	then
		COMMAND="mkdir -p /mnt/acserver_mount && mount -o ro,noload,noacl,loop,offset=1048576 /sources/acserver.dd /mnt/acserver_mount && ./tests/end-to-end.py --config /config/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /mnt --tools-directory ./tools && umount /mnt/acserver_mount && rmdir /mnt/acserver_mount";

	elif [[ ${TEST_NAME} == *\-nsrlsvr ]];
	then
		# Install nsrlsvr and give it 3 minutes to start-up before running the output end-to-end test.
		COMMAND="./config/linux/ubuntu_install_nsrlsvr.sh && sleep 3m && ${COMMAND}";

	elif [[ ${TEST_NAME} == *\-redis ]];
	then
		# TODO: add support for Redis tests
		continue;
	fi
	echo "Running ${TEST_CASE} end-to-end test: ${TEST_NAME}";

	mkdir -p ${TEST_RESULTS}/${TEST_NAME}/profiling;

	docker run -v "${TEST_CONFIGURATIONS}:/config:z" -v "${TEST_RESULTS}/${TEST_NAME}:/home/test/plaso/plaso-out:z" -v "${TEST_SOURCES}:/sources:z" log2timeline/plaso /bin/bash -c "${COMMAND}";

	echo "";

	rm -rf ${TEST_RESULTS}/${TEST_NAME};
done

exit ${EXIT_SUCCESS};


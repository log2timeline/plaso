#!/bin/bash
#
# Script to run Plaso end-to-end tests with Docker.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

TEST_SET="greendale";

TEST_DATA="test_data";
TEST_RESULTS="test_results";

if [[ ! -d ${TEST_DATA} ]];
then
	echo "Missing test data directory: ${TEST_DATA}";

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

# First run the extract_and_output end-to-end tests.
for CONFIG_FILE in ../jenkins/${TEST_SET}/*.ini;
do
	TEST_NAME=`basename ${CONFIG_FILE} | sed 's/\.ini$//'`;
	TEST_CASE=`grep -e '^case=' ${CONFIG_FILE} | sed 's/^case=//'`;

	if [[ ${TEST_CASE} == "extract_and_output" ]];
	then
		if [[ ${TEST_NAME} == *\-redis ]];
		then
			# TODO: add support for Redis tests
			continue;
		fi
		echo "Running extract_and_output end-to-end test: ${TEST_SET}/${TEST_NAME}";

		mkdir -p ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}/profiling;

		# Note that output is mapped to /home/test/plaso/plaso-out to ensure files
		# created by the end-to-end.py script are stored outside the container.

		docker run -v "${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}:/home/test/plaso/plaso-out:z" -v "${TEST_DATA}/${TEST_SET}:/sources:z" log2timeline/plaso ./tests/end-to-end.py --config config/jenkins/${TEST_SET}/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /sources --tools-directory ./tools

		echo "";
	fi
done

# The output end-to-end tests depend on the output of the student-pc1
# extract_and_output test.
for CONFIG_FILE in ../jenkins/${TEST_SET}/*.ini;
do
	TEST_NAME=`basename ${CONFIG_FILE} | sed 's/\.ini$//'`;
	TEST_CASE=`grep -e '^case=' ${CONFIG_FILE} | sed 's/^case=//'`;

	if [[ ${TEST_CASE} == "output" ]];
	then
		if [[ ${TEST_NAME} == *_elastic ]];
		then
			# TODO: add support for psort+elasticsearch tests
			continue;

		elif [[ ${TEST_NAME} == *\-nsrlsvr ]];
		then
			# TODO: add support for psort+nsrlsvr tests
			continue;

		elif [[ ${TEST_NAME} == *_opensearch ]];
		then
			# TODO: add support for psort+opensearch tests
			continue;
		fi
		echo "Running output end-to-end test: ${TEST_SET}/${TEST_NAME}";

		mkdir -p ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME};

		# Note that output is mapped to /home/test/plaso/plaso-out to ensure files
		# created by the end-to-end.py script are stored outside the container.

		docker run -v "${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}:/home/test/plaso/plaso-out:z" -v "${TEST_RESULTS}/${TEST_SET}/student-pc1:/sources:z" log2timeline/plaso ./tests/end-to-end.py --config config/jenkins/${TEST_SET}/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /sources --tools-directory ./tools

		echo "";
	fi
done

exit ${EXIT_SUCCESS};


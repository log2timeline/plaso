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
		# Note that output is mapped to /home/test/plaso/plaso-out to ensure files
		# created by the end-to-end.py script are stored outside the container.

		COMMAND="./tests/end-to-end.py --config config/jenkins/${TEST_SET}/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /sources --tools-directory ./tools";

		if [[ ${TEST_NAME} == *\-mounted ]];
		then
			# TODO: add support for mounted tests
			continue;
		fi
		if [[ ${TEST_NAME} == *\-redis ]];
		then
			# TODO: add support for Redis tests
			continue;
		fi
		echo "Running extract_and_output end-to-end test: ${TEST_SET}/${TEST_NAME}";

		mkdir -p ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}/profiling;

		docker run -v "${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}:/home/test/plaso/plaso-out:z" -v "${TEST_DATA}/${TEST_SET}:/sources:z" log2timeline/plaso /bin/bash -c "${COMMAND}";

		echo "";

		# The output end-to-end tests depend on the output of the student-pc1
		# extract_and_output test.

		if [[ ${TEST_NAME} != "student-pc1" ]];
		then
			rm -rf ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME};
		fi
	fi
done

for CONFIG_FILE in ../jenkins/${TEST_SET}/*.ini;
do
	TEST_NAME=`basename ${CONFIG_FILE} | sed 's/\.ini$//'`;
	TEST_CASE=`grep -e '^case=' ${CONFIG_FILE} | sed 's/^case=//'`;

	if [[ ${TEST_CASE} == "output" ]];
	then
		# Note that output is mapped to /home/test/plaso/plaso-out to ensure files
		# created by the end-to-end.py script are stored outside the container.

		COMMAND="./tests/end-to-end.py --config config/jenkins/${TEST_SET}/${TEST_NAME}.ini --references-directory test_data/end_to_end --results-directory plaso-out --sources-directory /sources --tools-directory ./tools";

		if [[ ${TEST_NAME} == *_elastic || ${TEST_NAME} == *_elastic_ts ]];
		then
			# Install Elasticsearch 7 and give it 3 minutes to start-up before running the output end-to-end test.
			COMMAND="./config/linux/ubuntu_install_elasticsearch7.sh && sleep 3m && ${COMMAND}";

		elif [[ ${TEST_NAME} == *\-nsrlsvr ]];
		then
			# Install nsrlsvr and give it 3 minutes to start-up before running the output end-to-end test.
			COMMAND="./config/linux/ubuntu_install_nsrlsvr.sh && sleep 3m && ${COMMAND}";

		elif [[ ${TEST_NAME} == *_opensearch || ${TEST_NAME} == *_opensearch_ts ]];
		then
			# Install OpenSearch and give it 3 minutes to start-up before running the output end-to-end test.
			COMMAND="./config/linux/ubuntu_install_opensearch.sh && sleep 3m && ${COMMAND}";
		fi
		echo "Running output end-to-end test: ${TEST_SET}/${TEST_NAME}";

		mkdir -p ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME};

		docker run -v "${TEST_RESULTS}/${TEST_SET}/${TEST_NAME}:/home/test/plaso/plaso-out:z" -v "${TEST_RESULTS}/${TEST_SET}/student-pc1:/sources:z" log2timeline/plaso /bin/bash -c "${COMMAND}";

		echo "";

		rm -rf ${TEST_RESULTS}/${TEST_SET}/${TEST_NAME};
	fi
done

exit ${EXIT_SUCCESS};


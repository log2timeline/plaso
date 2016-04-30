#!/bin/bash
#
# Script to generate test files.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

TEST_DIRECTORY="/tmp/test";

if ! test -x "setup.py";
then
	echo "Unable to find: ./setup.py";

	exit ${EXIT_FAILURE};
fi

rm -rf build/ dist/;

./setup.py -q sdist;

if test $? -ne ${EXIT_SUCCESS};
then
	echo "Unable to run: ./setup.py sdist";

	exit ${EXIT_FAILURE};
fi

SDIST_PACKAGE=`ls -1 dist/plaso-*.tar.gz | head -n1 | sed 's?^dist/??'`;

if ! test "dist/${SDIST_PACKAGE}";
then
	echo "Missing sdist package: dist/${SDIST_PACKAGE}";

	exit ${EXIT_FAILURE};
fi

OLD_PWD=${PWD};

mkdir ${TEST_DIRECTORY};

if ! test -d "${TEST_DIRECTORY}";
then
	echo "Missing test directory: ${TEST_DIRECTORY}";

	exit ${EXIT_FAILURE};
fi

cp dist/${SDIST_PACKAGE} ${TEST_DIRECTORY};

cd ${TEST_DIRECTORY};

if ! test -f "${SDIST_PACKAGE}";
then
	echo "Missing sdist package: ${SDIST_PACKAGE}";

	exit ${EXIT_FAILURE};
fi

tar xfv ${SDIST_PACKAGE};

SOURCE_DIRECTORY=${SDIST_PACKAGE/.tar.gz/};

if ! test -d "./${SOURCE_DIRECTORY}";
then
	echo "Missing source directory: ${SOURCE_DIRECTORY}";

	exit ${EXIT_FAILURE};
fi

cp -rf ${SOURCE_DIRECTORY}/* .;

TEST_FILE="psort_test.json.plaso";

PYTHONPATH=. ./tools/log2timeline.py --buffer_size=300 ${TEST_FILE} test_data/syslog;
PYTHONPATH=. ./tools/log2timeline.py -z Iceland ${TEST_FILE} test_data/syslog;

cd ${OLD_PWD};

mv ${TEST_DIRECTORY}/${TEST_FILE} test_data/;

rm -rf ${TEST_DIRECTORY};


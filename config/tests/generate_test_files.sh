#!/bin/bash
#
# Script to generate test files.

EXIT_SUCCESS=0
EXIT_FAILURE=1

set -e

TEST_DIRECTORY="/tmp/test"

rm -rf .tox build dist

cp MANIFEST.test_data.in MANIFEST.in

python -m build --sdist

git checkout MANIFEST.in

if [ $? -ne ${EXIT_SUCCESS} ];
then
	echo "Unable to create sdist package"

	exit ${EXIT_FAILURE}
fi

SDIST_PACKAGE=$(ls -1 dist/plaso-*.tar.gz | head -n1 | sed 's?^dist/??')

if [ ! -f "dist/${SDIST_PACKAGE}" ]
then
	echo "Missing sdist package: dist/${SDIST_PACKAGE}"

	exit ${EXIT_FAILURE}
fi

mkdir ${TEST_DIRECTORY}

if [ ! -d "${TEST_DIRECTORY}" ]
then
	echo "Missing test directory: ${TEST_DIRECTORY}"

	exit ${EXIT_FAILURE}
fi

cp dist/${SDIST_PACKAGE} ${TEST_DIRECTORY}

pushd ${TEST_DIRECTORY}

if [ ! -f "${SDIST_PACKAGE}" ]
then
	echo "Missing sdist package: ${SDIST_PACKAGE}"

	exit ${EXIT_FAILURE}
fi

tar xfv ${SDIST_PACKAGE}

SOURCE_DIRECTORY=${SDIST_PACKAGE/.tar.gz/}

if [ ! -d "./${SOURCE_DIRECTORY}" ]
then
	echo "Missing source directory: ${SOURCE_DIRECTORY}"

	exit ${EXIT_FAILURE}
fi

cp -rf ${SOURCE_DIRECTORY}/* .

TEST_FILE="psort_test.plaso"

# Syslog does not contain a year we must pass preferred year to prevent the parser failing early on non-leap years.
PYTHONPATH=. python ./tools/log2timeline.py --buffer_size=300 --quiet --preferred_year 2012 --storage-file ${TEST_FILE} test_data/syslog
PYTHONPATH=. python ./tools/log2timeline.py --quiet --timezone=Iceland --preferred_year 2012 --storage-file ${TEST_FILE} test_data/syslog

cat > tagging.txt <<EOI
anacron1
  body contains 'anacron'

exit1
  body contains ' exit '

repeated
  body contains 'last message repeated'
EOI

PYTHONPATH=. python ./tools/psort.py --analysis tagging --output-format=null --tagging-file=tagging.txt ${TEST_FILE}

# Run tagging twice.
cat > tagging.txt <<EOI
anacron2
  body contains 'anacron'

exit2
  body contains ' exit '

repeated
  body contains 'last message repeated'
EOI

PYTHONPATH=. python ./tools/psort.py --analysis tagging --output-format=null --tagging-file=tagging.txt ${TEST_FILE}

mv ${TEST_FILE} ${OLD_PWD}/test_data/

TEST_FILE="pinfo_test.plaso"

PYTHONPATH=. python ./tools/log2timeline.py --partition=all --quiet --storage-file ${TEST_FILE} test_data/tsk_volume_system.raw

mv ${TEST_FILE} ${OLD_PWD}/test_data/

popd

rm -rf ${TEST_DIRECTORY}


#!/bin/bash
#
# Script to generate test files.

EXIT_SUCCESS=0
EXIT_FAILURE=1

set -e

TEST_DIRECTORY="/tmp/test"

if [ -d "${TEST_DIRECTORY}" ]
then
    echo "Test directory: ${TEST_DIRECTORY} already exists"

    exit ${EXIT_FAILURE}
fi

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

cp dist/${SDIST_PACKAGE} ${TEST_DIRECTORY}

OLD_PWD=${PWD}

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

# Syslog does not contain a year we must pass preferred year to prevent the
# parser failing early on non-leap years.

PYTHONPATH=. python ./plaso/scripts/log2timeline.py \
    --buffer_size=300 \
    --quiet \
    --preferred-year 2012 \
    --storage-file ${TEST_FILE} \
    test_data/syslog/syslog

PYTHONPATH=. python ./plaso/scripts/log2timeline.py \
    --quiet \
    --timezone=Iceland \
    --preferred-year 2012 \
    --storage-file ${TEST_FILE} \
    test_data/syslog/syslog

cat > tagging.txt <<EOI
anacron1
  body contains 'anacron'

exit1
  body contains ' exit '

repeated
  body contains 'last message repeated'
EOI

PYTHONPATH=. python ./plaso/scripts/psort.py \
    --analysis tagging \
    --output-format=null \
    --tagging-file=tagging.txt \
    ${TEST_FILE}

# Run tagging twice.
cat > tagging.txt <<EOI
anacron2
  body contains 'anacron'

exit2
  body contains ' exit '

repeated
  body contains 'last message repeated'
EOI

PYTHONPATH=. python ./plaso/scripts/psort.py \
    --analysis tagging \
    --output-format=null \
    --tagging-file=tagging.txt \
    ${TEST_FILE}

cp ${TEST_FILE} ${OLD_PWD}/test_data/

PYTHONPATH=. ./plaso/scripts/pinfo.py \
    --report file_hashes \
    --output-format json \
    ${TEST_FILE} > ${TEST_FILE}.file_hashes.json

cp ${TEST_FILE}.file_hashes.json ${OLD_PWD}/test_data/

PYTHONPATH=. ./plaso/scripts/pinfo.py \
    --report file_hashes \
    --output-format markdown \
    ${TEST_FILE} > ${TEST_FILE}.file_hashes.md

cp ${TEST_FILE}.file_hashes.md ${OLD_PWD}/test_data/

PYTHONPATH=. ./plaso/scripts/pinfo.py \
    --report file_hashes \
    --output-format text \
    ${TEST_FILE} > ${TEST_FILE}.file_hashes.txt

cp ${TEST_FILE}.file_hashes.txt ${OLD_PWD}/test_data/

TEST_FILE="pinfo_test.plaso"

PYTHONPATH=. python ./plaso/scripts/log2timeline.py \
    --partition=all \
    --quiet \
    --storage-file ${TEST_FILE} \
    test_data/tsk_volume_system.raw

cp ${TEST_FILE} ${OLD_PWD}/test_data/

PYTHONPATH=. ./plaso/scripts/pinfo.py \
    --sections events,reports,sessions,warnings \
    --output-format text \
    ${TEST_FILE} > ${TEST_FILE}.output.txt

cp ${TEST_FILE}.output.txt ${OLD_PWD}/test_data/

popd

# TODO: automatically update:
# test_data/end_to_end/dynamic.log
# test_data/end_to_end/dynamic_time_zone.log
# test_data/end_to_end/dynamic_without_dynamic_time.log
# test_data/end_to_end/json.log
# test_data/end_to_end/json_line.log
# test_data/end_to_end/l2tcsv.log
# test_data/end_to_end/l2tcsv_time_zone.log
# test_data/end_to_end/l2ttln.log
# test_data/end_to_end/rawpy.log
# test_data/end_to_end/tln.log

rm -rf ${TEST_DIRECTORY}

exit ${EXIT_SUCCESS}

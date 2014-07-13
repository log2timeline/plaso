#!/bin/bash
# A small script that runs all tests
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

COVERAGE="/usr/bin/coverage";
COVERAGE_REPORT="tests-coverage.txt";
PYTHON="/usr/bin/python";

if ! test -x "${PYTHON}";
then
  # MSYS-MinGW allows to run the script using the Windows Python version.
  PYTHON="/c/python27/python.exe";
fi

if ! test -x "${PYTHON}";
then
  echo "Unable to locate Python interpreter."
  echo "";
  exit ${EXIT_FAILURE};
fi

if test -x "${COVERAGE}";
then
  rm -f .coverage ${COVERAGE_REPORT};
fi

# Run the tests in a specific order.
SUBDIRS="lib serializer winreg filters classifier engine events parsers output analysis frontend";

for SUBDIR in ${SUBDIRS};
do
  TEST_FILES=`find "plaso/${SUBDIR}" -name "*_test.py" | grep -v "\/build\/"`;

  for TEST_FILE in ${TEST_FILES};
  do
    if test ${TEST_FILE} = "plaso/parsers/pcap_test.py";
    then
      continue;
    fi

    echo "---+ ${TEST_FILE} +---"

    if test -x "${COVERAGE}";
    then
      PYTHONPATH=. ${COVERAGE} run -a ${TEST_FILE};
    else
      PYTHONPATH=. ${PYTHON} ${TEST_FILE};
    fi

    if test $? -ne 0;
    then
      echo "TEST FAILED: ${TEST_FILE}.";
      echo "";
      echo "Stopping further testing.";
      echo "";
      exit ${EXIT_FAILURE};
    fi
    echo "";
  done
done

if test -x "${COVERAGE}";
then
  echo "Writing tests coverage report: ${COVERAGE_REPORT}"; 
  SITE_PACKAGES="/usr/lib/python2.7/site-packages";
  ${COVERAGE} report -m --omit="${SITE_PACKAGES}/*,*_test.py" > ${COVERAGE_REPORT};

  rm -f .coverage
fi

exit ${EXIT_SUCCESS};


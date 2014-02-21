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

# Run the tests in a specific order.
SUBDIRS="lib serializer winreg filters classifier collector parsers output analysis frontend";

for SUBDIR in ${SUBDIRS};
do
  TEST_FILES=`find "plaso/${SUBDIR}" -name "*_test.py" | grep -v "\/build\/"`;

  for TEST_FILE in ${TEST_FILES};
  do
    if test ${TEST_FILE} = "plaso/parsers/pcap_test.py";
    then
      continue;
    fi

    echo "---+ ${TEST_FILE} +---";
    PYTHONPATH=. /usr/bin/python ${TEST_FILE};

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

exit ${EXIT_SUCCESS};


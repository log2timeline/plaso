#!/bin/bash
# A small script that contains common functions for code review checks.
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

linter()
{
  # Examples of the output of "git status -s"
  # If a file is added:
  # A utils/common.sh
  # If a file is modified:
  # M utils/common.sh
  # If a file is renamed:
  # R utils/common.sh -> utils/uncommon.sh
  # If a file is modified and renamed:
  # RM utils/common.sh -> utils/uncommon.sh
  AWK_SCRIPT="if (\$1 == \"A\" || \$1 == \"AM\" || \$1 == \"M\") { print \$2; } else if (\$1 == \"R\" || \$1 == \"RM\") { print \$4; }";

  # First find all files that need linter
  FILES=`git status -s | grep -v "^?" | awk "{ ${AWK_SCRIPT} }" | grep "\.py$"`;

  PYLINT_VERSION=`pylint --version 2> /dev/null | grep 'pylint' | sed 's/^pylint \(.*\),/\1/'`;

  RESULT=`echo -e "${PYLINT_VERSION}\n1.1.0" | sort -V | head -n1`;

  if test "${RESULT}" = "${PYLINT_VERSION}";
  then
    PYLINTRC="utils/pylintrc";
  else
    PYLINTRC="utils/pylintrc-1.1.0";
  fi
  LINTER="pylint --rcfile=${PYLINTRC}";

  echo "Run through pylint.";

  for FILE in ${FILES};
  do
    if test "${FILE}" = "setup.py" || test "${FILE}" = "utils/upload.py" ;
    then
      echo "  -- Skipping: ${FILE} --"
      continue
    fi

    if test `echo ${FILE} | tail -c8` == "_pb2.py" ;
    then
      echo "Skipping compiled protobufs: ${FILE}"
      continue
    fi

    echo "  -- Checking: ${FILE} --"
    $LINTER "${FILE}"

    if test $? -ne 0 ;
    then
      echo "Fix linter errors before proceeding."
      return ${EXIT_FAILURE};
    fi
  done

  if test $? -ne 0 ;
  then
    return ${EXIT_FAILURE};
  fi

  echo "Linter clear.";

  return ${EXIT_SUCCESS};
}

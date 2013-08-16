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

  if [ "x`which pylint`" == "x" ]
  then
    LINTER="pychecker -Q -f --only -6 --unusednames"

    echo "Run through pychecker.";
  else
    # TODO: Re-enable pylint again, disabling for a while to not make lint CL
    # larger than it already is.
    LINTER="pylint --rcfile=utils/pylintrc"

    echo "Run through pylint.";
  fi

  for FILE in ${FILES};
  do
    if [ "${FILE}" = "setup.py" ] || [ "${FILE}" = "utils/upload.py" ];
    then
      echo "  -- Skipping: ${FILE} --"
      continue
    fi

    if [ `echo ${FILE} | tail -c8` == "_pb2.py" ];
    then
      echo "Skipping compiled protobufs: ${FILE}"
      continue
    fi

    echo "  -- Checking: ${FILE} --"
    $LINTER "${FILE}"

    if [ $? -ne 0 ];
    then
      echo "Fix linter errors before proceeding."
      return ${EXIT_FAILURE};
    fi

    # Run through "line width" checker since that is not covered by the linter.
    python utils/linecheck.py "${FILE}"

    if [ $? -ne 0 ]
    then
      echo "Fix line width errors before proceeding."
      return ${EXIT_FAILURE};
    fi
  done

  if [ $? -ne 0 ]
  then
    return ${EXIT_FAILURE};
  fi

  echo "Linter clear.";

  return ${EXIT_SUCCESS};
}

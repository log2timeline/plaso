#!/bin/bash
# A small script that updates a change list for code review.
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
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
CACHE_PARAM="";
CL_NUMBER="";

while test $# -gt 0;
do
  case $1 in
  --nobrowser | --no-browser | --no_browser )
    BROWSER_PARAM="--no_oauth2_webbrowser";
    shift;
    ;;

  *)
    CL_NUMBER=$1;
    shift
    ;;
  esac
done

if test -z "${CL_NUMBER}";
then
  if test -f ._code_review_number;
  then
    CL_NUMBER=`cat ._code_review_number`
    RESULT=`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`;

    if ! test -z "${RESULT}";
    then
      echo "File ._code_review_number exists but contains an incorrect CL number.";

      exit ${EXIT_FAILURE};
    fi
  fi
fi

if test -z "${CL_NUMBER}";
then
  echo "Usage: ./${SCRIPTNAME} [--nobrowser] [CL_NUMBER]";
  echo "";
  echo "  CL_NUMBER: optional change list (CL) number that is to be updated.";
  echo "             If no CL number is provided the value is read from:";
  echo "             ._code_review_number";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

if [ ! -f "utils/common.sh" ];
then
  echo "Missing common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

# Check for double status codes, upload.py cannot handle these correctly.
STATUS_CODES=`git status -s | cut -b1,2 | grep '\S\S' | grep -v '??' | sort | uniq`;

if ! test -z "${STATUS_CODES}";
then
  echo "Update aborted - detected double git status codes."
  echo "Run: 'git stash && git stash pop'.";

  exit ${EXIT_FAILURE};
fi

# Check if the linting is correct.
if ! linter;
then
  echo "Update aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

# Check if all the tests pass.
if test -e run_tests.py;
then
  echo "Running tests.";
  python run_tests.py

  if test $? -ne 0;
  then
    echo "Update aborted - fix the issues reported by the failing test.";

    exit ${EXIT_FAILURE};
  fi
fi

# Check if we need to set --cache.
STATUS_CODES=`git status -s | cut -b1,2 | sed 's/\s//g' | sort | uniq`;

for STATUS_CODE in ${STATUS_CODES};
do
  if test "${STATUS_CODE}" = "A";
  then
    CACHE_PARAM="--cache";
  fi
done

python utils/upload.py \
    --oauth2 ${BROWSER_PARAM} -y -i ${CL_NUMBER} ${CACHE_PARAM} \
    -t "Uploading changes made to code." -m "Code updated.";

exit ${EXIT_SUCCESS};

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
CL_NUMBER=0;

while test $# -gt 0;
do
  case $1 in
  --cache )
    CACHE_PARAM="--cache";
    shift;
    ;;

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

if test -z $CL_NUMBER;
then
  if test -f ._code_review_number;
  then
    CL_NUMBER=`cat ._code_review_number`

    if test "x`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`" != "x";
    then
      echo "File ._code_review_number exists but contains an invalid CL number.";
      exit ${EXIT_FAILURE};
    fi
  fi
fi

if test -z $CL_NUMBER;
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

if ! linter;
then
  echo "Update aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

echo "Run tests.";
python run_tests.py

if test $? -ne 0;
then
  echo "Tests failed, not updating change list: ${CL_NUMBER}";
  exit ${EXIT_FAILURE};
else
  echo "Tests succeeded, updating change list: ${CL_NUMBER}";
fi

python utils/upload.py \
    --oauth2 ${BROWSER_PARAM} -y -i ${CL_NUMBER} ${CACHE_PARAM} \
    -t "Uploading changes made to code." -m "Code updated.";

exit ${EXIT_SUCCESS};

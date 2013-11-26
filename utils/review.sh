#!/bin/bash
# A small script that submits a code for code review.
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

EXIT_SUCCESS=0;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
CACHE_PARAM="";
USE_CL_FILE=1;

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

  --noclfile | --no-clfile | --no_clfile )
    USE_CL_FILE=0;
    shift;
    ;;

  *)
    REVIEWER=$1;
    shift
    ;;
  esac
done

if test -z $REVIEWER;
then
  echo "Usage: ./${SCRIPTNAME} [--nobrowser] [--noclfile] REVIEWER";
  echo "";
  echo "  REVIEWER: the email address of the reviewer that is registered with:"
  echo "            https://codereview.appspot.com";
  echo "";

  exit ${EXIT_MISSING_ARGS};
fi

if ! test -f "utils/common.sh";
then
  echo "Missing common functions, are you in the wrong directory?";
  exit ${EXIT_FAILURE};
fi

. utils/common.sh

# First find all files that need linter
linter

if test $? -ne 0;
then
  exit ${EXIT_FAILURE};
else
  echo "Linter clear.";
fi

echo "Run tests.";
python run_tests.py

if test $? -ne 0;
then
  echo "Tests failed, not submitting for review.";
  exit ${EXIT_FAILURE};
else
  echo "Tests all came up clean. Send for review.";
fi

MISSING_TESTS="";
FILES=`git status -s | grep -v "^?" | awk '{if ($1 != 'D') { print $2;}}' | grep "\.py$" | grep -v "_test.py$"`
for CHANGED_FILE in ${FILES};
do
  TEST_FILE=`echo ${CHANGED_FILE} | sed -e 's/\.py//g'`
  if ! test -f "${TEST_FILE}_test.py";
  then
    MISSING_TESTS="${MISSING_TESTS} + ${CHANGED_FILE}"
  fi
done

if test "x${MISSING_TESTS}" == "x";
then
  MISSING_TEST_FILES=".";
else
  MISSING_TEST_FILES="These files are missing unit tests:
${MISSING_TESTS}
  ";
fi

echo -n "Short description of code review request: ";
read DESCRIPTION
TEMP_FILE=`mktemp .tmp_plaso_code_review.XXXXXX`;

if test "x${BROWSER_PARAM}" != "x";
then
  echo "You need to visit: https://codereview.appspot.com/get-access-token";
  echo "and copy+paste the access token to the window (no prompt)";
fi

python utils/upload.py \
    --oauth2 ${BROWSER_PARAM} -y --cc log2timeline-dev@googlegroups.com \
    -r ${REVIEWER} -m "${MISSING_TEST_FILES}" -t "${DESCRIPTION}" \
    --send_mail ${CACHE_PARAM} | tee ${TEMP_FILE};

CL=`cat ${TEMP_FILE} | grep codereview.appspot.com | awk -F '/' '/created/ {print $NF}'`;
cat ${TEMP_FILE};
rm -f ${TEMP_FILE};

echo "";

if test -z ${CL};
then
  echo "Unable to upload code change for review.";
  exit ${EXIT_FAILURE};

elif test ${USE_CL_FILE} -ne 0;
then
  echo ${CL} > ._code_review_number;
  echo "Code review number: ${CL} is saved, so no need to include that in future updates/submits.";
fi

exit ${EXIT_SUCCESS};

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

EXIT_FAILURE=1;
EXIT_MISSING_ARGS=2;
EXIT_SUCCESS=0;

SCRIPTNAME=`basename $0`;

BROWSER_PARAM="";
if test "$1" == "--nobrowser";
then
  BROWSER_PARAM="--no_oauth2_webbrowser";
  shift
fi

if test $# -ne 1;
then
  if test $# -eq 0 && test -f ._code_review_number;
  then
    CL_NUMBER=`cat ._code_review_number`
    if test "x`echo ${CL_NUMBER} | sed -e 's/[0-9]//g'`" != "x";
    then
      echo "File ._code_review_number exists but contains wrong CL number.";
      exit ${EXIT_FAILURE};
    fi
  else
    echo "Usage: ./${SCRIPTNAME} [CL_NUMBER]";
    echo "";
    echo " CL_NUMBER: optional change list (CL) number that is to be updated.";
    echo "            if no CL number is provided the value is read from:";
    echo "            ._code_review_number";
    echo "";

    exit ${EXIT_MISSING_ARGS};
  fi
else
  CL_NUMBER=$1;
fi


if ! test -f "utils/common.sh";
then
  echo "Unable to find common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

# Source the common library.
. utils/common.sh

if ! linter;
then
  echo "Sumbit aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

echo "Running tests."
python run_tests.py

if test $? -ne 0;
then
  echo "Sumbit aborted - fix the issues reported by the failing test.";

  exit ${EXIT_FAILURE};
fi

echo "All came out clean, let's submit the code."

URL_CODEREVIEW="https://codereview.appspot.com";

# Get the description of the change list
if test "x`which json_xs`" != "x";
then
  DESCRIPTION=`curl -s ${URL_CODEREVIEW}/api/${CL_NUMBER} | json_xs | grep '"subject"' | awk -F '"' '{print $(NF-1)}'`;
else
  DESCRIPTION=`curl ${URL_CODEREVIEW}/${CL_NUMBER}/ -s | grep "Issue ${CL_NUMBER}" | awk -F ':' '{print $2}' | tail -1`;
fi

if test "x${DESCRIPTION}" == "x";
then
  echo "Submit aborted - unable to find change list with number: ${CL_NUMBER}.";

  exit ${EXIT_FAILURE};
fi

# Check if the local repo is in sync with the origin
git fetch

if test $? -ne 0;
then
  echo "Sumbit aborted - unable to fetch updates from origin repo";

  exit ${EXIT_FAILURE};
fi

NUMBER_OF_CHANGES=`git log HEAD..origin/master --oneline | wc -l`;

if test $? -ne 0;
then
  echo "Sumbit aborted - unable to determine if local repo is in sync with origin";

  exit ${EXIT_FAILURE};
fi

if test ${NUMBER_OF_CHANGES} -ne 0;
then
  echo "Sumbit aborted - local repo out of sync with origin, run: 'git stash && git pull && git stash pop' before sumbit.";

  exit ${EXIT_FAILURE};
fi

# Update the version information
echo "Updating version information to match today's date."
DATE_NOW=`date +"%Y%m%d"`
sed -i -e "s/^VERSION_DATE.*$/VERSION_DATE = '${DATE_NOW}'/g" plaso/lib/engine.py

python utils/upload.py --oauth2 $BROWSER_PARAM -y -i ${CL_NUMBER} -t "Submitted." -m "Code Submitted." --send_mail

git commit -a -m "Code review: ${CL_NUMBER}: ${DESCRIPTION}";
git push

if test -f "~/codereview_upload_cookies";
then
  curl -b ~/.codereview_upload_cookies ${URL_CODEREVIEW}/${CL_NUMBER}/close -d  ''
else
  echo "Could not find an authenticated session to codereview. You need to"
  echo "manually close the ticket on the code review site."
fi

if test -f "._code_review_number";
then
  rm -f ._code_review_number
fi

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
if [ "$1" == "--nobrowser" ];
then
  BROWSER_PARAM="--no_oauth2_webbrowser";
  shift
fi

if [ -f ._code_review_number ];
then
  CL_NUMBER=`cat ._code_review_number`
  if [ "x`echo $CL_NUMBER | sed -e 's/[0-9]//g'`" != "x" ];
  then
    echo "File ._code_review_number exists but contains wrong CL number.";
    exit 1;
  fi
else
  # Check usage
  if [ $# -ne 1 ]
  then
    echo "Usage: ./${SCRIPTNAME} CL#";
    echo "";
    echo " CL#: the change list number that is to be submitted.";
    echo "";

    exit ${EXIT_MISSING_ARGS};
  fi

  CL_NUMBER=$1;
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

if [ $? -ne 0 ];
then
  echo "Tests failed, not submitting.";

  exit ${EXIT_FAILURE};
fi

echo "All came out clean, let's update the code review.";

python utils/upload.py --oauth2 $BROWSER_PARAM -y -i ${CL_NUMBER} -t "Uploading changes made to code." -m "Code updated.";

exit ${EXIT_SUCCESS};

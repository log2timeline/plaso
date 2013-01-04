#!/bin/bash
# A small script that submits a code for code review.
#
# Copyright 2012 Google Inc. All Rights Reserved.
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

if [ ! -f "utils/common.sh" ];
then
  echo "Missing common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

# First find all files that need linter
echo "Run through pychecker.";
linter

if [ $? -ne 0 ];
then
  exit ${EXIT_FAILURE};
fi

echo "Linter clear.";

echo "Run tests.";
./utils/run_tests.sh

if [ $? -ne 0 ];
then
  echo "Tests failed, not submitting.";

  exit ${EXIT_FAILURE};
fi

echo "All came out clean, let's submit the code.";

python utils/upload.py -y -i ${CL_NUMBER} -t "." -m ".";

exit ${EXIT_SUCCESS};

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

# Check usage
if [ $# -ne 1 ]
then
  echo "Wrong USAGE: `basename $0` REVIEWER"
  exit 1
fi

REVIEWER=$1

if [ ! -f "utils/common.sh" ]
then
  echo "Missing common functions, are you in the wrong directory?"
  exit 1
fi

. utils/common.sh

# First find all files that need linter
linter

if [ $? -ne 0 ]
then
  exit 1
fi

echo "Linter clear."

echo "Run tests."
python run_tests.py

if [ $? -ne 0 ]
then
  echo "Tests failed, not submitting for review."
  exit 2
fi

echo "Tests all came up clean. Send for review."

MISSING_TESTS=""
FILES=`git status -s | grep -v "^?" | awk '{if ($1 != 'D') { print $2;}}' | grep "\.py$" | grep -v "_test.py$"`
for file_change in $FILES
do
  FILE=`echo ${file_change} | sed -e 's/\.py//g'`
  if [ ! -f "${FILE}_test.py" ]
  then
    MISSING_TESTS="$MISSING_TESTS + ${file_change}"
  fi
done

if [ "x$MISSING_TESTS" == "x" ]
then
  M="."
else
  M="These files are missing unit tests:
$MISSING_TESTS
  "
fi

echo -n "Short description of code review request: "
read DESC
T1=`mktemp .tmp_plaso_code_review.XXXXXX`
python utils/upload.py --oauth2 -y --cc log2timeline-dev@googlegroups.com -r $REVIEWER -m "$M" -t "$DESC" --send_mail | tee $T1

CL=`cat $T1 | grep codereview.appspot.com | awk -F '/' '/created/ {print $NF}'`
cat $T1
rm -f $T1
echo ""
echo $CL > ._code_review_number
echo "Code review number: ${CL} is saved, so no need to include that in future updates/submits."

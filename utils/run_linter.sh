#!/bin/bash
# A small script that runs the linter on all files.
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
EXIT_SUCCESS=0;

export PYTHONPATH=../

if [ ! -f "utils/common.sh" ];
then
  echo "Missing common functions, are you in the wrong directory?";

  exit ${EXIT_FAILURE};
fi

. utils/common.sh

if ! linter;
then
  echo "Aborted - fix the issues reported by the linter.";

  exit ${EXIT_FAILURE};
fi

exit ${EXIT_SUCCESS};


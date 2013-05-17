#!/bin/bash
# Script that prepares the codebase for building a binary distribution
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

# Remove support for hachoir which is GPLv2 and cannot be distributed
# in binary form. Leave the formatter because it does not link in the
# hachoir code.

rm -f parsers/hachoir*

sed -i -e "/import hachoir/d" parsers/__init__.py

SED_SCRIPT="
/_slow': \[/ {
:loop
  /'\],/ !{
      N
      b loop
  }
  d
}";

sed -i -e "${SED_SCRIPT}" frontend/presets.py

exit ${EXIT_SUCCESS};


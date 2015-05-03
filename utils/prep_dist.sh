#!/bin/bash
# Script that prepares the codebase for building a binary distribution

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

# Remove support for hachoir which is GPLv2 and cannot be distributed
# in binary form. Leave the formatter because it does not link in the
# hachoir code.

rm -f plaso/parsers/hachoir*

sed -i"~" -e '/import hachoir/d' plaso/parsers/__init__.py

SED_SCRIPT="
/_slow': \[/ {
:loop
  /'\],/ !{
      N
      b loop
  }
  d
}";

sed -i"~" -e "${SED_SCRIPT}" plaso/frontend/presets.py

sed -i"~" '/hachoir_/,/^$/d' plaso/dependencies.py

exit ${EXIT_SUCCESS};


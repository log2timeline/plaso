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

sed -i"~" -e "${SED_SCRIPT}" plaso/parsers/presets.py

sed -i"~" '/hachoir_/d' plaso/dependencies.py

if ! test -d ../l2tdevtools;
then
	echo "Unable to locate l2tdevtools.";

	exit ${EXIT_FAILURE};
fi

rm -rf config/licenses

mkdir config/licenses

DEPENDENCIES=`cat ../l2tdevtools/data/presets.ini | grep -A1 '\[plaso\]' | tail -n1 | sed 's/projects: //' | tr ',' ' '`;

for DEPENDENCY in ${DEPENDENCIES};
do
	cp "../l2tdevtools/data/licenses/LICENSE.${DEPENDENCY}" config/licenses/
done

rm -f config/licenses/LICENSE.hachoir-*
rm -f config/licenses/LICENSE.guppy
rm -f config/licenses/LICENSE.libexe
rm -f config/licenses/LICENSE.libwrc
rm -f config/licenses/LICENSE.mock
rm -f config/licenses/LICENSE.pbr

PYTHONPATH=../l2tdevtools python ../l2tdevtools/tools/update-dependencies.py

exit ${EXIT_SUCCESS};


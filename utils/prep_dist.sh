#!/bin/bash
# Script that prepares the codebase for building a binary distribution

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

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

# Remove debug, test and yet unused dependencies.
rm -f config/licenses/LICENSE.guppy
rm -f config/licenses/LICENSE.libexe
rm -f config/licenses/LICENSE.libwrc
rm -f config/licenses/LICENSE.mock
rm -f config/licenses/LICENSE.pbr

PYTHONPATH=../l2tdevtools python ../l2tdevtools/tools/update-dependencies.py

exit ${EXIT_SUCCESS};


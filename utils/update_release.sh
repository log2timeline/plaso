#!/bin/bash
#
# Script that makes changes in preparation of a new release, such as updating
# the version and documentation.

EXIT_FAILURE=1;
EXIT_SUCCESS=0;

VERSION=$(date -u +"%Y%m%d")

# Update the Python module version.
sed "s/__version__ = '[0-9]*'/__version__ = '${VERSION}'/" -i plaso/__init__.py

# Update the version in the pyproject configuration.
sed "s/version = \"[0-9]*\"/version = \"${VERSION}\"/" -i pyproject.toml

# Ensure shebangs of Python scripts are consistent.
find . -name \*.py -exec sed '1s?^#!.*$?#!/usr/bin/env python3?' -i {} \;

find plaso/scripts -name \*.py -exec grep -H -L '#!/usr/bin/env python3' {} \; | grep -v -e '__init__.py'
find tests -name \*.py -exec grep -H -L '#!/usr/bin/env python3' {} \; | grep -v -e '__init__.py' -e 'test_lib.py'

# Update the version in the dpkg configuration files.
DPKG_DATE=$(date -R)

cat > config/dpkg/changelog << EOT
plaso (${VERSION}-1) unstable; urgency=low

  * Auto-generated

 -- Log2Timeline maintainers <log2timeline-maintainers@googlegroups.com>  ${DPKG_DATE}
EOT

# Regenerate the parser and plugins documentation.
PYTHONPATH=. ./plaso/scripts/log2timeline.py --parsers list --use-markdown > docs/sources/user/Parsers-and-plugins.md

# Regenerate the supported formats documentation.
# TODO: generate supported formats.
# PYTHONPATH=. ./utils/export_supported_formats.py > docs/sources/Supported-formats.md

# Regenerate the API documentation.
tox -edocs

# Check for unused entries in plaso/data/formatters/*.yaml
./utils/check_unused_formatter_definitions.sh

# Check for unused entries in plaso/data/timeliner.yaml
./utils/check_unused_timeliner_entries.sh

exit ${EXIT_SUCCESS};


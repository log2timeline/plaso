#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to check for the availability and version of dependencies."""

import sys

# Change PYTHONPATH to include dependencies.
sys.path.insert(0, '.')

import utils.dependencies  # pylint: disable=wrong-import-position


if __name__ == '__main__':
  dependency_helper = utils.dependencies.DependencyHelper()

  if not dependency_helper.CheckDependencies():
    build_instructions_url = (
        'https://plaso.readthedocs.io/en/latest/sources/user/Users-Guide.html')

    print('See: {0:s} on how to set up plaso.'.format(build_instructions_url))
    print('')

    sys.exit(1)

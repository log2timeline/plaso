#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to check for the availability and version of dependencies."""

from __future__ import print_function
import sys

# Change PYTHONPATH to include dependencies.
sys.path.insert(0, u'.')

import utils.dependencies  # pylint: disable=wrong-import-position


if __name__ == u'__main__':
  dependency_helper = utils.dependencies.DependencyHelper()

  if not dependency_helper.CheckDependencies():
    build_instructions_url = (
        u'https://github.com/log2timeline/plaso/wiki/Users-Guide')

    print(u'See: {0:s} on how to set up plaso.'.format(build_instructions_url))
    print(u'')

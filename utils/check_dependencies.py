#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to check for the availability and version of dependencies."""

from __future__ import print_function
import sys

# Change PYTHONPATH to include plaso.
sys.path.insert(0, u'.')

import plaso.dependencies


if __name__ == u'__main__':
  if not plaso.dependencies.CheckDependencies(latest_version_check=True):
    build_instructions_url = (
        u'https://sites.google.com/a/kiddaland.net/plaso/developer'
        u'/building-the-tool')

    print(u'See: {0:s} on how to set up plaso.'.format(build_instructions_url))
    print(u'')

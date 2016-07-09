# -*- coding: utf-8 -*-
"""This file contains a function to expand Windows environment variables."""

import re

from plaso.lib import py2to3


# TODO: Remove this file once we have a better replacement for it, either
# to use the artifact library or dfVFS, since this is part of both of these
# libraries.

# Taken from: https://code.google.com/p/grr/source/browse/lib/artifact_lib.py
def ExpandWindowsEnvironmentVariables(path, path_attributes):
  """Expands a path based on Windows environment variables.

  Args:
    path (str): path before being expanded.
    path_attributes (dict[str, str]): path attributes e.g.
        {'SystemRoot': 'C:\\Windows'}

  Returns:
    str: path expanded based on path attributes.
  """
  if path_attributes is None:
    path_attributes = {}

  path_attributes = {
      key.lower(): value for key, value in path_attributes.items()}

  environment_variable_regexp = re.compile(r'%([^%]+?)%')

  offset = 0
  expanded_path_fragments = []
  for match in environment_variable_regexp.finditer(path):
    expanded_path_fragments.append(path[offset:match.start()])

    environment_variable = match.group(1)

    replacement_value = path_attributes.get(environment_variable.lower(), None)
    if isinstance(replacement_value, py2to3.STRING_TYPES):
      expanded_path_fragments.append(replacement_value)
    else:
      expanded_path_fragments.append(u'%{0:s}%'.format(environment_variable))

    offset = match.end()

  expanded_path_fragments.append(path[offset:])

  return u''.join(expanded_path_fragments)

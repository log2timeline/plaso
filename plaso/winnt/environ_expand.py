# -*- coding: utf-8 -*-
"""This file contains a method to expand Windows environment variables."""

import re

from plaso.lib import py2to3


# TODO: Remove this file once we have a better replacement for it, either
# to use the artifact library or dfVFS, since this is part of both of these
# libraries.

# Taken from: https://code.google.com/p/grr/source/browse/lib/artifact_lib.py
def ExpandWindowsEnvironmentVariables(data_string, path_attributes):
  """Take a string and expand any windows environment variables.

  Args:
    data_string: A string, e.g. "%SystemRoot%\\LogFiles"
    path_attributes: dictionary of path attributes.

  Returns:
    A string with available environment variables expanded.
  """
  if path_attributes is None:
    path_attributes = {}

  win_environ_regex = re.compile(r'%([^%]+?)%')
  components = []
  offset = 0
  for match in win_environ_regex.finditer(data_string):
    components.append(data_string[offset:match.start()])

    kb_value = path_attributes.get(match.group(1).lower(), None)
    if isinstance(kb_value, py2to3.STRING_TYPES) and kb_value:
      components.append(kb_value)
    else:
      components.append(u'%%{0:s}%%'.format(match.group(1)))
    offset = match.end()
  components.append(data_string[offset:])    # Append the final chunk.
  return u''.join(components)

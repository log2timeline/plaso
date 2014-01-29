#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a method to expand Windows environment variables."""
import re

# TODO: Remove this file once we have a better replacement for it, either
# to use the artifact library or dfVFS, since this is part of both of these
# libraries.

# Taken from: https://code.google.com/p/grr/source/browse/lib/artifact_lib.py
def ExpandWindowsEnvironmentVariables(data_string, knowledge_base):
  """Take a string and expand any windows environment variables.

  Args:
    data_string: A string, e.g. "%SystemRoot%\\LogFiles"
    knowledge_base: A knowledgebase object.

  Returns:
    A string with available environment variables expanded.
  """
  win_environ_regex = re.compile(r'%([^%]+?)%')
  components = []
  offset = 0
  for match in win_environ_regex.finditer(data_string):
    components.append(data_string[offset:match.start()])

    kb_value = getattr(
        knowledge_base, match.group(1).lower(), None)
    if isinstance(kb_value, basestring) and kb_value:
      components.append(kb_value)
    else:
      components.append(u'%%{:s}%%'.format(match.group(1)))
    offset = match.end()
  components.append(data_string[offset:])    # Append the final chunk.
  return u''.join(components)

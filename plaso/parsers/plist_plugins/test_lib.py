#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Plist plugin related functions and classes for testing."""

from plaso.parsers import test_lib
from plaso.pvfs import pfile


class PlistPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a plist plugin."""

  def _ParsePlistFileWithPlugin(
      self, parser_object, plugin_object, path, plist_name):
    """Parses a file using the parser and plugin object.

    Args:
      parser_object: the parser object.
      plugin_object: the pluging object.
      path: the path of the file to parse.
      plist_name: the name of the plist to parse.

    Returns:
      A generator of event objects as returned by the plugin.
    """
    path_spec = pfile.PFileResolver.CopyPathToPathSpec('OS', path)
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)

    file_object = file_entry.Open()
    top_level_object = parser_object.GetTopLevel(file_object)
    self.assertNotEquals(top_level_object, None)

    event_generator = plugin_object.Process(plist_name, top_level_object)
    self.assertNotEquals(event_generator, None)

    return event_generator

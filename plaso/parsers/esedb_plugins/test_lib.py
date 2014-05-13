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
"""ESEDB plugin related functions and classes for testing."""

import pyesedb

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers import test_lib


class EseDbPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for ESE database based plugins."""

  def _OpenEseDbFile(self, path):
    """Opens an ESE database file and returns back a pyesedb.file object."""
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    file_object = file_entry.GetFileObject()
    esedb_file = pyesedb.file()

    esedb_file.open_file_object(file_object)

    return esedb_file

  def _ParseEseDbFileWithPlugin(self, path, plugin_object):
    """Parses a file as an ESE database file and returns an event generator.

    Args:
      path: The path to the ESE database test file.
      plugin_object: The plugin object that is used to extract an event
                     generator.

    Returns:
      A generator of event objects as returned by the plugin.
    """
    esedb_file = self._OpenEseDbFile(path)
    event_generator = plugin_object.Process(database=esedb_file)

    self.assertNotEquals(event_generator, None)

    return event_generator

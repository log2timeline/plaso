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
"""OLECF plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers import test_lib

import pyolecf


class OleCfPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for OLE CF based plugins."""

  def _OpenOleCfFile(self, path, codepage='cp1252'):
    """Opens an OLE compound file and returns back a pyolecf.file object."""
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    file_object = file_entry.GetFileObject()
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(codepage)

    olecf_file.open_file_object(file_object)

    return olecf_file

  def _ParseOleCfFileWithPlugin(self, path, plugin_object):
    """Parses a file as an OLE compound file and returns an event generator.

    Args:
      path: The path to the OLE CF test file.
      plugin_object: The plugin object that is used to extract an event
                     generator.

    Returns:
      A generator of event objects as returned by the plugin.
    """
    olecf_file = self._OpenOleCfFile(path)

    # Get a list of all root items from the OLE CF file.
    root_item = olecf_file.root_item
    item_names = [item.name for item in root_item.sub_items]

    event_generator = plugin_object.Process(
        root_item=root_item, item_names=item_names)

    self.assertNotEquals(event_generator, None)

    return event_generator

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
"""Windows Registry plugin related functions and classes for testing."""

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.parsers import test_lib
from plaso.winreg import winregistry


class RegistryPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for a Windows Registry plugin."""

  def _GetKeyFromFile(self, path, key_path):
    """Retrieves a Windows Registry key from a file.

    Args:
      path: the path of the file.
      key_path: the path of the key to parse.

    Returns:
      A Windows Registry key (instance of WinRegKey).
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    registry = winregistry.WinRegistry(winregistry.WinRegistry.BACKEND_PYREGF)
    winreg_file = registry.OpenFile(file_entry, codepage='cp1252')
    return winreg_file.GetKeyByPath(key_path)

  def _ParseKeyWithPlugin(self, plugin_object, winreg_key):
    """Parses a key within a Windows Registry file using the plugin object.

    Args:
      plugin_object: the plugin object.
      winreg_key: the Windows Registry Key.

    Returns:
      A generator of event objects as returned by the plugin.
    """
    self.assertNotEquals(winreg_key, None)

    event_generator = plugin_object.Process(key=winreg_key)
    self.assertNotEquals(event_generator, None)

    return event_generator

  def _TestRegvalue(self, event_object, identifier, expected_value):
    """Tests a specific 'regvalue' attribute within the event object.

    Args:
      event_object: the event object (instance of EventObject).
      identifier: the identifier of the 'regvalue' attribute.
      expected_value: the expected value of the 'regvalue' attribute.
    """
    self.assertTrue(hasattr(event_object, 'regvalue'))
    self.assertIn(identifier, event_object.regvalue)
    self.assertEquals(event_object.regvalue[identifier], expected_value)

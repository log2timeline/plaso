#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the USBStor Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import usbstor


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = usbstor.USBStorPlugin()

  def testProcess(self):
    """Tests the Process function."""
    knowledge_base_values = {'current_control_set': u'ControlSet001'}
    test_file_entry = self._GetTestFileEntryFromPath(['SYSTEM'])
    key_path = u'\\ControlSet001\\Enum\\USBSTOR'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, knowledge_base_values=knowledge_base_values,
        file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 3)

    event_object = event_objects[0]

    self.assertEquals(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEquals(event_object.parser, self._plugin.plugin_name)

    self.assertEquals(event_object.timestamp, 1333794697640871)

    expected_value = u'Disk&Ven_HP&Prod_v100w&Rev_1024'
    self._TestRegvalue(event_object, u'subkey_name', expected_value)

    self._TestRegvalue(event_object, u'device_type', u'Disk')
    self._TestRegvalue(event_object, u'vendor', u'Ven_HP')
    self._TestRegvalue(event_object, u'product', u'Prod_v100w')
    self._TestRegvalue(event_object, u'revision', u'Rev_1024')

    expected_msg = (
        u'[{0:s}] '
        u'device_type: Disk '
        u'friendly_name: HP v100w USB Device '
        u'product: Prod_v100w '
        u'revision: Rev_1024 '
        u'serial: AA951D0000007252&0 '
        u'subkey_name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
        u'vendor: Ven_HP').format(key_path)

    expected_msg_short = (
        u'[{0:s}] '
        u'device_type: Disk '
        u'friendly_name: HP v100w USB D...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()

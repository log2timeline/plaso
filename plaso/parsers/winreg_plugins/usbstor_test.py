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

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import event
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import usbstor


class USBStorPlugin(test_lib.RegistryPluginTestCase):
  """Tests for the USBStor Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.current_control_set = 'ControlSet001'
    self._plugin = usbstor.USBStorPlugin(pre_obj=pre_obj)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['SYSTEM'])
    # TODO: change into: u'{current_control_set}\\Enum\\USBSTOR'?
    key_path = u'\\ControlSet001\\Enum\\USBSTOR'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_generator = self._ParseKeyWithPlugin(self._plugin, winreg_key)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 3)

    event_object = event_objects[0]

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

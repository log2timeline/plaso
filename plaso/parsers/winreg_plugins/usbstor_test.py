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
"""This file contains tests for the USBStor plugin."""

import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import usbstor
from plaso.winreg import winregistry


class TestUSBStor(unittest.TestCase):
  """Test for parsing a USBStor Registry key."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._pre_obj = preprocess.PlasoPreprocess()
    self._pre_obj.current_control_set = 'ControlSet001'

    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'SYSTEM')
    file_object = open(test_file, 'rb')
    self.winreg_file = registry.OpenFile(file_object, codepage='cp1252')

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testUSBStorPlugin(self):
    """Test the user assist plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\ControlSet001\\Enum\\USBSTOR')
    plugin = usbstor.USBStorPlugin(None, self._pre_obj, None)
    entries = list(plugin.Process(key))

    self.assertEquals(len(entries), 3)
    self.assertEquals(entries[0].timestamp, 1333794697640871)

    # Disk&Ven_HP&Prod_v100w&Rev_1024
    self.assertEquals(entries[0].regvalue[u'device_type'], 'Disk')
    self.assertEquals(entries[0].regvalue[u'vendor'], 'Ven_HP')
    self.assertEquals(entries[0].regvalue[u'product'], 'Prod_v100w')
    self.assertEquals(entries[0].regvalue[u'revision'], 'Rev_1024')

    expected_string = (
      u'[\\ControlSet001\\Enum\\USBSTOR] '
      u'device_type: Disk '
      u'friendly_name: HP v100w USB Device '
      u'product: Prod_v100w '
      u'revision: Rev_1024 '
      u'serial: AA951D0000007252&0 '
      u'subkey_name: Disk&Ven_HP&Prod_v100w&Rev_1024 '
      u'vendor: Ven_HP')

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_string)


if __name__ == '__main__':
  unittest.main()

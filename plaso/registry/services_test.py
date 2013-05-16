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
"""This file contains tests for Services registry parsing in Plaso."""
import unittest

from plaso.lib import eventdata
from plaso.registry import services
from plaso.registry import test_lib


class TestServicesRegistry(unittest.TestCase):
  """The unit test for Services registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue('Type', '\x02\x00\x00\x00', 4, 123))
    values.append(test_lib.TestRegValue('Start', '\x02\x00\x00\x00', 4, 127))
    values.append(test_lib.TestRegValue(
        'ErrorControl', '\x01\x00\x00\x00', 4, 131))
    values.append(test_lib.TestRegValue(
        'Group', 'Pnp Filter'.encode('utf_16_le'), 1, 140))
    values.append(test_lib.TestRegValue(
        'DisplayName', 'Test Driver'.encode('utf_16_le'), 1, 160))
    values.append(test_lib.TestRegValue(
        'DriverPackageId',
        'testdriver.inf_x86_neutral_dd39b6b0a45226c4'.encode('utf_16_le'), 1,
        180))
    values.append(test_lib.TestRegValue(
        'ImagePath', 'C:\\Dell\\testdriver.sys'.encode('utf_16_le'), 1, 200))

    self.regkey = test_lib.TestRegKey(
        '\\ControlSet001\\services\\TestDriver', 1346145829002031, values, 1456)

  def testServices(self):
    """Test the ServicesPlugin."""
    plugin = services.ServicesPlugin(None, None)
    entries = list(plugin.Process(self.regkey))
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

    line = (u'[\\ControlSet001\\services\\TestDriver] DisplayName: Test Driver '
            'DriverPackageId: testdriver.inf_x86_neutral_dd39b6b0a45226c4 Error'
            'Control: Normal (1) Group: Pnp Filter ImagePath: REGALERT Driver '
            'not in system32: C:\\Dell\\testdriver.sys Start: REGALERT Unusual '
            'Start for Driver: Auto Start (2) Type: File System Driver (0x2)')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Tue, 28 Aug 2012 09:23:49 GMT.
    self.assertEquals(entries[0].timestamp, 1346145829002031)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)
    self.assertEquals(entries[0].regalert, True)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a test for MS Office MRUs plugin in Plaso."""
import os
import unittest

from plaso.formatters import winreg   # pylint: disable-msg=W0611
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import officemru
from plaso.winreg import winregistry

__author__ = 'David Nides (david.nides@gmail.com)'


class RegistryOfficeMRUTest(unittest.TestCase):
  """The unit test for IE Typed URLS plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER-WIN7.DAT')
    file_object = open(test_file, 'rb')
    self.winreg_file = registry.OpenFile(file_object, codepage='cp1252')

  def testOfficeMRU(self):
    """Test the Typed URLS plugin."""
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU')
    plugin = officemru.MSWord2010FileMRU(None, None, None)
    entries = list(plugin.Process(key))

    # Tue Mar 13 18:27:15.083000 UTC 2012
    expected_timestamp = 1331663235083000

    self.assertEquals(entries[0].timestamp, expected_timestamp)

    self.assertTrue(
        u'Item 1' in entries[0].regvalue)

    expected_value_data = (
        u'[F00000000][T01CD0146EA1EADB0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        u'SA-23E Mitchell-Hyundyne Starfury.docx')

    self.assertEquals(entries[0].regvalue[u'Item 1'], expected_value_data)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])

    expected_string = (
        u'[\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU] '
        u'Item 1: [F00000000][T01CD0146EA1EADB0][O00000000]*'
        u'C:\\Users\\nfury\\Documents\\StarFury\\StarFury\\'
        u'SA-23E Mitchell-Hyundyne Starfury.docx')

    self.assertEquals(msg, expected_string)


if __name__ == '__main__':
  unittest.main()

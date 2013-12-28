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
"""This file contains tests for Less Frequently Used Keys parsing in Plaso."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.winreg_plugins import lfu
from plaso.winreg import cache
from plaso.winreg import test_lib


class TestBootExecuteRegistry(unittest.TestCase):
  """The unit test for BootExecute registry value parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None
    values = []
    values.append(test_lib.TestRegValue(
        'BootExecute', 'autocheck autochk *\x00'.encode('utf_16_le'), 7, 123))
    values.append(test_lib.TestRegValue(
        'CriticalSectionTimeout', '2592000'.encode('utf_16_le'), 1, 153))
    values.append(test_lib.TestRegValue('ExcludeFromKnownDlls',
                                        '\x00'.encode('utf_16_le'), 7, 163))
    values.append(test_lib.TestRegValue('GlobalFlag', '0'.encode('utf_16_le'),
                                        1, 173))
    values.append(test_lib.TestRegValue('HeapDeCommitFreeBlockThreshold',
                                        '0'.encode('utf_16_le'), 1, 183))
    values.append(test_lib.TestRegValue('HeapDeCommitTotalFreeThreshold',
                                        '0'.encode('utf_16_le') , 1, 203))
    values.append(test_lib.TestRegValue('HeapSegmentCommit',
                                        '0'.encode('utf_16_le'), 1, 213))
    values.append(test_lib.TestRegValue('HeapSegmentReserve',
                                        '0'.encode('utf_16_le'), 1, 223))
    values.append(test_lib.TestRegValue('NumberOfInitialSessions',
                                        '2'.encode('utf_16_le'), 1, 243))
    self.regkey = test_lib.TestRegKey(
        '\\ControlSet001\\Control\\Session Manager', 1346445929000000, values,
        153)
    self.preprocess = preprocess.PlasoPreprocess()
    self.registry_cache = cache.WinRegistryCache(None, 'SYSTEM')
    self.registry_cache.attributes['current_control_set'] = 'ControlSet001'

  def testBootExecute(self):
    plugin = lfu.BootExecutePlugin(None, self.preprocess, self.registry_cache)
    entries = list(plugin.Process(self.regkey))

    line1 = (u'[\\ControlSet001\\Control\\Session Manager] BootExecute: '
             'autocheck autochk *')
    line2 = (u'[\\ControlSet001\\Control\\Session Manager] '
             'CriticalSectionTimeout: 2592000 ExcludeFromKnownDlls: [] '
             'GlobalFlag: 0 HeapDeCommitFre'
             'eBlockThreshold: 0 HeapDeCommitTotalFreeThreshold: 0 HeapSegment'
             'Commit: 0 HeapSegmentReserve: 0 NumberOfInitialSessions: 2')

    self.assertEquals(len(entries), 2)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line1)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[1])
    self.assertEquals(msg, line2)


class TestBootVerificationRegistry(unittest.TestCase):
  """The unit test for BootVerification key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'ImagePath',
        'C:\\WINDOWS\\system32\\googleupdater.exe'.encode('utf_16_le'), 1,
        123))
    self.regkey = test_lib.TestRegKey(
        '\\ControlSet001\\Control\\BootVerificationProgram',
        1346445929000000, values, 153)
    self.preprocess = preprocess.PlasoPreprocess()
    self.registry_cache = cache.WinRegistryCache(None, 'SYSTEM')
    self.registry_cache.attributes['current_control_set'] = 'ControlSet001'

  def testBootVerification(self):
    plugin = lfu.BootVerificationPlugin(
        None, self.preprocess, self.registry_cache)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\\ControlSet001\\Control\\BootVerificationProgram] Boot'
            'Verification: REGALERT ImagePath: C:\\WINDOWS\\system32\\google'
            'updater.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)
    self.assertEquals(entries[0].regalert, True)


if __name__ == '__main__':
  unittest.main()

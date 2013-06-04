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
"""This file contains tests for Run Keys registry parsing in Plaso."""
import unittest

from plaso.formatters import winreg
from plaso.lib import eventdata
from plaso.registry import run
from plaso.winreg import test_lib


class TestRunNtuserRegistry(unittest.TestCase):
  """The unit test for NTUSER Run key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'ctfmon.exe', 'C:\\WINDOWS\\system32\\ctfmon.exe'.encode('utf_16_le'),
        1, 123))
    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
        1346445929000000, values, 153)

  def testRunNtuser(self):
    plugin = run.RunNtuserPlugin(None, None)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\Software\Microsoft\Windows\CurrentVersion\Run] ctfmon.exe: '
            'C:\WINDOWS\system32\ctfmon.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT.
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)


class TestRunOnceNtuserRegistry(unittest.TestCase):
  """The unit test for NTUSER RunOnce key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'googleupdater.exe',
        'C:\\WINDOWS\\system32\\googleupdater.exe'.encode('utf_16_le'), 1,
        123))
    self.regkey = test_lib.TestRegKey(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
        1346445929000000, values, 153)

  def testRunOnceNtuser(self):
    plugin = run.RunOnceNtuserPlugin(None, None)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\Software\Microsoft\Windows\CurrentVersion\RunOnce] google'
            'updater.exe: C:\WINDOWS\system32\googleupdater.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT.
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)


class TestRunSoftwareRegistry(unittest.TestCase):
  """The unit test for Software Run key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'ctfmon.exe', 'C:\\WINDOWS\\system32\\ctfmon.exe'.encode('utf_16_le'),
        1, 123))
    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Windows\\CurrentVersion\\Run', 1346445929000000, values,
        153)

  def testRunSoftware(self):
    plugin = run.RunSoftwarePlugin(None, None)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\Microsoft\Windows\CurrentVersion\Run] ctfmon.exe: '
            'C:\WINDOWS\system32\ctfmon.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT.
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)


class TestRunOnceSoftwareRegistry(unittest.TestCase):
  """The unit test for Software RunOnce key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    values = []
    values.append(test_lib.TestRegValue(
        'googleupdater.exe',
        'C:\\WINDOWS\\system32\\googleupdater.exe'.encode('utf_16_le'), 1,
        123))
    self.regkey = test_lib.TestRegKey(
        '\\Microsoft\\Windows\\CurrentVersion\\RunOnce', 1346445929000000,
        values, 153)

  def testRunOnceSoftware(self):
    plugin = run.RunOnceSoftwarePlugin(None, None)
    entries = list(plugin.Process(self.regkey))

    line = (u'[\Microsoft\Windows\CurrentVersion\RunOnce] googleupdater.exe: '
            'C:\WINDOWS\system32\googleupdater.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: Fri, 31 Aug 2012 20:45:29 GMT.
    self.assertEquals(entries[0].timestamp, int(1346445929 * 1e6))
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, line)


if __name__ == '__main__':
  unittest.main()

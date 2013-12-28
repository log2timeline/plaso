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
"""This file contains tests for Run Keys registry parsing in Plaso."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import eventdata
from plaso.parsers.winreg_plugins import run
from plaso.pvfs import utils
from plaso.winreg import winregistry


class TestRunNtuserRegistry(unittest.TestCase):
  """The unit tests for NTUSER Run[Once] key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'NTUSER-RunTests.DAT')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

  def testRunNtuser(self):
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run')
    plugin = run.RunNtuserPlugin(None, None, None)
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\Run] '
        u'Sidebar: %ProgramFiles%\\Windows Sidebar\\Sidebar.exe /autoRun')

    self.assertEquals(len(entries), 1)
    # Timestamp is: 2012-04-05T17:03:53.992061+00:00
    self.assertEquals(entries[0].timestamp, 1333645433992061)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_line)

  def testRunOnceNtuser(self):
    key = self.winreg_file.GetKeyByPath(
        '\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce')
    plugin = run.RunOnceNtuserPlugin(None, None, None)
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce] '
        u'mctadmin: C:\\Windows\\System32\\mctadmin.exe')

    self.assertEquals(len(entries), 1)
    # Timestamp is: 2012-04-05T17:03:53.992061+00:00
    self.assertEquals(entries[0].timestamp, 1333645433992061)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_line)


class TestRunSoftwareRegistry(unittest.TestCase):
  """The unit tests for Software Run[Once] key registry parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    test_file = os.path.join('test_data', 'SOFTWARE-RunTests')
    file_entry = utils.OpenOSFileEntry(test_file)
    self.winreg_file = registry.OpenFile(file_entry, codepage='cp1252')

  def testRunSoftware(self):
    key = self.winreg_file.GetKeyByPath(
        '\\Microsoft\\Windows\\CurrentVersion\\Run')
    plugin = run.RunSoftwarePlugin(None, None, None)
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Microsoft\\Windows\\CurrentVersion\\Run] VMware Tools: '
        u'\"C:\\Program Files\\VMware\\VMware Tools\\VMwareTray.exe\"')

    self.assertEquals(len(entries), 3)
    # Timestamp is: 2011-09-16T20:57:09.067575+00:00
    self.assertEquals(entries[0].timestamp, 1316206629067575)
    self.assertEquals(entries[1].timestamp, 1316206629067575)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_line)

  def testRunOnceSoftware(self):
    key = self.winreg_file.GetKeyByPath(
        '\\Microsoft\\Windows\\CurrentVersion\\RunOnce')
    plugin = run.RunOnceSoftwarePlugin(None, None, None)
    entries = list(plugin.Process(key))

    expected_line = (
        u'[\\Microsoft\\Windows\\CurrentVersion\\RunOnce] '
        u'*WerKernelReporting: %SYSTEMROOT%\\SYSTEM32\\WerFault.exe -k -rq')

    self.assertEquals(len(entries), 1)
    # Timestamp is: 2012-04-06T14:07:27.750000+00:00
    self.assertEquals(entries[0].timestamp, 1333721247750000)
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(entries[0])
    self.assertEquals(msg, expected_line)


if __name__ == '__main__':
  unittest.main()

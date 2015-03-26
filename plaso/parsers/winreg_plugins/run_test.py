#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Run Windows Registry plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.parsers.winreg_plugins import run
from plaso.parsers.winreg_plugins import test_lib


class RunNtuserPlugintest(test_lib.RegistryPluginTestCase):
  """Tests for the Run Windows Registry plugin on the User hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = run.RunUserPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['NTUSER-RunTests.DAT'])
    key_path = u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    # Timestamp is: 2012-04-05T17:03:53.992061+00:00
    self.assertEqual(event_object.timestamp, 1333645433992061)

    expected_msg = (
        u'[{0:s}] Sidebar: %ProgramFiles%\\Windows Sidebar\\Sidebar.exe '
        u'/autoRun').format(key_path)
    expected_msg_short = (
        u'[{0:s}] Sidebar: %ProgramFiles%\\Wind...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class RunOnceNtuserPlugintest(test_lib.RegistryPluginTestCase):
  """Tests for the RunOnce Windows Registry plugin on the User hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = run.RunUserPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['NTUSER-RunTests.DAT'])
    key_path = u'\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    # Timestamp is: 2012-04-05T17:03:53.992061+00:00
    self.assertEqual(event_object.timestamp, 1333645433992061)

    expected_msg = (
        u'[{0:s}] mctadmin: C:\\Windows\\System32\\mctadmin.exe').format(
            key_path)
    expected_msg_short = (
        u'[{0:s}] mctadmin: C:\\Windows\\Sys...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


class RunSoftwarePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Run Windows Registry plugin on the Software hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = run.RunSoftwarePlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['SOFTWARE-RunTests'])
    key_path = u'\\Microsoft\\Windows\\CurrentVersion\\Run'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 3)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    # Timestamp is: 2011-09-16T20:57:09.067575+00:00
    self.assertEqual(event_object.timestamp, 1316206629067575)

    expected_msg = (
        u'[{0:s}] VMware Tools: \"C:\\Program Files\\VMware\\VMware Tools'
        u'\\VMwareTray.exe\"').format(key_path)
    expected_msg_short = (
        u'[{0:s}] VMware Tools: \"C:\\Program Files\\VMwar...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    self.assertEqual(event_objects[1].timestamp, 1316206629067575)


class RunOnceSoftwarePluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the RunOnce Windows Registry plugin on the Software hive."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = run.RunSoftwarePlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath(['SOFTWARE-RunTests'])
    key_path = u'\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    # Timestamp is: 2012-04-06T14:07:27.750000+00:00
    self.assertEqual(event_object.timestamp, 1333721247750000)

    expected_msg = (
        u'[{0:s}] *WerKernelReporting: %SYSTEMROOT%\\SYSTEM32\\WerFault.exe '
        u'-k -rq').format(key_path)
    expected_msg_short = (
        u'[{0:s}] *WerKernelReporting: %SYSTEMROOT%...').format(key_path)

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()

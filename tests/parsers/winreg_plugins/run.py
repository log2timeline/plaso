#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Run Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import run

from tests.parsers.winreg_plugins import test_lib


class AutoRunsPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the auto rus Windows Registry plugin."""

  def testProcessNtuserRun(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-RunTests.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Run')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 1)

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    # Timestamp is: 2012-04-05T17:03:53.992061+00:00
    self.assertEqual(event_object.timestamp, 1333645433992061)

    expected_message = (
        u'[{0:s}] Sidebar: %ProgramFiles%\\Windows Sidebar\\Sidebar.exe '
        u'/autoRun').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessNtuserRunOnce(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-RunTests.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'RunOnce')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 1)

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-05 17:03:53.992061')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] mctadmin: C:\\Windows\\System32\\mctadmin.exe').format(
            key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

  def testProcessSoftwareRun(self):
    """Tests the Process function on a Run key."""
    test_file_entry = self._GetTestFileEntry([u'SOFTWARE-RunTests'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Run')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 3)

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 20:57:09.067575')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] VMware Tools: \"C:\\Program Files\\VMware\\VMware Tools'
        u'\\VMwareTray.exe\"').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-09-16 20:57:09.067575')
    self.assertEqual(storage_writer.events[1].timestamp, expected_timestamp)

  def testProcessSoftwareRunOnce(self):
    """Tests the Process function on a RunOnce key."""
    test_file_entry = self._GetTestFileEntry([u'SOFTWARE-RunTests'])
    key_path = (
        u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'RunOnce')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin_object = run.AutoRunsPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin_object, file_entry=test_file_entry)

    self.assertEqual(len(storage_writer.events), 1)

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, plugin_object.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-04-06 14:07:27.750000')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_message = (
        u'[{0:s}] *WerKernelReporting: %SYSTEMROOT%\\SYSTEM32\\WerFault.exe '
        u'-k -rq').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

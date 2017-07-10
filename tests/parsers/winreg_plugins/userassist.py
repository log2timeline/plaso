#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry plugin."""

import unittest

from plaso.formatters import userassist  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import userassist

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


class UserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the UserAssist Windows Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER.DAT'])
  def testProcessOnWinXP(self):
    """Tests the Process function on a Windows XP Registry file."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\UserAssist\\{75048700-EF1F-11D0-9888-006097DEACF9}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = userassist.UserAssistPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 14)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:11:22.811067')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_value_name = u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'
    self.assertEqual(event.value_name, expected_value_name)
    self.assertEqual(event.number_of_executions, 14)

    expected_message = (
        u'[{0:s}\\Count] '
        u'Value name: {1:s} '
        u'Count: 14').format(key_path, expected_value_name)
    expected_short_message = u'{0:s} Count: 14'.format(expected_value_name)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'NTUSER-WIN7.DAT'])
  def testProcessOnWin7(self):
    """Tests the Process function on a Windows 7 Registry file."""
    test_file_entry = self._GetTestFileEntry([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = userassist.UserAssistPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 61)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.assertEqual(event.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event.parser, plugin.plugin_name)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:49:37.078067')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_value_name = u'Microsoft.Windows.GettingStarted'
    self.assertEqual(event.value_name, expected_value_name)
    self.assertEqual(event.number_of_executions, 14)
    self.assertEqual(event.application_focus_count, 21)
    self.assertEqual(event.application_focus_duration, 420000)

    expected_message = (
        u'[{0:s}\\Count] '
        u'UserAssist entry: 1 '
        u'Value name: {1:s} '
        u'Count: 14 '
        u'Application focus count: 21 '
        u'Application focus duration: 420000').format(
            key_path, expected_value_name)
    expected_short_message = u'{0:s} Count: 14'.format(expected_value_name)

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry plugin."""

import unittest

from plaso.formatters import userassist as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import userassist

from tests.parsers.winreg_plugins import test_lib


class UserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the UserAssist Windows Registry plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = userassist.UserAssistPlugin()

  def testProcessOnWinXP(self):
    """Tests the Process function on a Windows XP Registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\UserAssist\\{75048700-EF1F-11D0-9888-006097DEACF9}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 14)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-08-04 15:11:22.811067')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    userassist_identifier = u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'
    expected_value = u'[Count: 14]'
    self._TestRegvalue(event_object, userassist_identifier, expected_value)

    userassist_value = u'{0:s}: {1:s}'.format(
        userassist_identifier, expected_value)
    expected_message = u'[{0:s}\\Count] {1:s}'.format(
        key_path, userassist_value)

    self._TestGetMessageStrings(
        event_object, expected_message, userassist_value)

  def testProcessOnWin7(self):
    """Tests the Process function on a Windows 7 Registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])
    key_path = (
        u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        u'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 61)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:49:37.078067')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    userassist_identifier = u'Microsoft.Windows.GettingStarted'
    expected_value = (
        u'[UserAssist entry: 1, Count: 14, Application focus count: 21, '
        u'Focus duration: 420000]')
    self._TestRegvalue(event_object, userassist_identifier, expected_value)

    userassist_value = u'{0:s}: {1:s}'.format(
        userassist_identifier, expected_value)
    expected_message = u'[{0:s}\\Count] {1:s}'.format(
        key_path, userassist_value)
    expected_short_message = u'{0:s}...'.format(userassist_value[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

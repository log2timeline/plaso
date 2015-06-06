#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UserAssist Windows Registry plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import userassist

from tests.parsers.winreg_plugins import test_lib


class UserAssistPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the UserAssist Windows Registry plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = userassist.UserAssistPlugin()

  def testProcessOnWinXP(self):
    """Tests the Process function on a Windows XP Registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER.DAT'])
    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        u'\\{75048700-EF1F-11D0-9888-006097DEACF9}')
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
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

    regvalue_identifier = u'UEME_RUNPIDL:%csidl2%\\MSN.lnk'
    expected_value = u'[Count: 14]'
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}\\Count] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    # The short message contains the first 76 characters of the key path.
    expected_msg_short = u'[{0:s}...'.format(key_path[:76])

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testProcessOnWin7(self):
    """Tests the Process function on a Windows 7 Registry file."""
    test_file_entry = self._GetTestFileEntryFromPath([u'NTUSER-WIN7.DAT'])

    key_path = (
        u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist'
        u'\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}')
    winreg_key = self._GetKeyFromFileEntry(test_file_entry, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 61)

    event_object = event_objects[0]

    self.assertEqual(event_object.pathspec, test_file_entry.path_spec)
    # This should just be the plugin name, as we're invoking it directly,
    # and not through the parser.
    self.assertEqual(event_object.parser, self._plugin.plugin_name)


    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-10 07:49:37.078067')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    regvalue_identifier = u'Microsoft.Windows.GettingStarted'
    expected_value = (
        u'[UserAssist entry: 1, Count: 14, Application focus count: 21, '
        u'Focus duration: 420000]')
    self._TestRegvalue(event_object, regvalue_identifier, expected_value)

    expected_msg = u'[{0:s}\\Count] {1:s}: {2:s}'.format(
        key_path, regvalue_identifier, expected_value)
    # The short message contains the first 76 characters of the key path.
    expected_msg_short = u'[{0:s}...'.format(key_path[:76])

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()

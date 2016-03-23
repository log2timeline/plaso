#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SAM Users Account information plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import sam_users

from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class SAMUsersWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests the SAM Users Account information plugin."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._plugin = sam_users.SAMUsersWindowsRegistryPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntryFromPath([u'SAM'])
    key_path = u'HKEY_LOCAL_MACHINE\\SAM\\SAM\\Domains\\Account\\Users'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key, file_entry=test_file_entry)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 7)

    event_object = event_objects[0]

    self._TestRegvalue(event_object, u'account_rid', 500)
    self._TestRegvalue(event_object, u'login_count', 6)
    self._TestRegvalue(event_object, u'username', u'Administrator')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-09-24 03:36:06.358837')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    expected_message = (
        u'[{0:s}] '
        u'account_rid: 500 '
        u'comments: Built-in account for administering the computer/domain '
        u'login_count: 6 '
        u'username: Administrator').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)

    # Test SAMUsersWindowsRegistryEvent
    event_object = event_objects[1]

    self.assertEqual(event_object.account_rid, 500)
    self.assertEqual(event_object.login_count, 6)
    self.assertEqual(event_object.username, u'Administrator')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-20 21:48:12.569244')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.LAST_LOGIN_TIME)

    expected_message = (
        u'[{0:s}] '
        u'Username: Administrator '
        u'Comments: Built-in account for administering the computer/domain '
        u'RID: 500 '
        u'Login count: 6').format(key_path)
    expected_short_message = (
        u'Administrator '
        u'RID: 500 '
        u'Login count: 6')

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SAM Users Account information plugin."""

import unittest

from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import sam_users

from tests import test_lib as shared_test_lib
from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class SAMUsersWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests the SAM Users Account information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SAM'])
  def testProcess(self):
    """Tests the Process function."""
    test_file_entry = self._GetTestFileEntry([u'SAM'])
    key_path = u'HKEY_LOCAL_MACHINE\\SAM\\SAM\\Domains\\Account\\Users'

    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)
    registry_key = win_registry.GetKeyByPath(key_path)

    plugin = sam_users.SAMUsersWindowsRegistryPlugin()
    storage_writer = self._ParseKeyWithPlugin(
        registry_key, plugin, file_entry=test_file_entry)

    self.assertEqual(storage_writer.number_of_events, 7)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self._TestRegvalue(event, u'account_rid', 500)
    self._TestRegvalue(event, u'login_count', 6)
    self._TestRegvalue(event, u'username', u'Administrator')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-09-24 03:36:06.358837')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_message = (
        u'[{0:s}] '
        u'account_rid: 500 '
        u'comments: Built-in account for administering the computer/domain '
        u'login_count: 6 '
        u'username: Administrator').format(key_path)
    expected_short_message = u'{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Test SAMUsersWindowsRegistryEvent.
    event = events[1]

    self.assertEqual(event.account_rid, 500)
    self.assertEqual(event.login_count, 6)
    self.assertEqual(event.username, u'Administrator')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-11-20 21:48:12.569244')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_LOGIN)

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

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

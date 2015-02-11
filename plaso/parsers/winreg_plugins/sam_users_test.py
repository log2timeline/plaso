#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Users key plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter
from plaso.lib import event
from plaso.lib import timelib_test
from plaso.parsers.winreg_plugins import test_lib
from plaso.parsers.winreg_plugins import sam_users


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class UsersPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the SAM Users key plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = sam_users.UsersPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['SAM'])
    key_path = u'\\SAM\\Domains\\Account\\Users'
    winreg_key = self._GetKeyFromFile(test_file, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, winreg_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 7)

    event_object = event_objects[0]

    self._TestRegvalue(event_object, u'account_rid', 500)
    self._TestRegvalue(event_object, u'login_count', 6)
    self._TestRegvalue(event_object, u'user_guid', u'000001F4')
    self._TestRegvalue(event_object, u'username', u'Administrator')

    expected_msg = (
        u'[\\SAM\\Domains\\Account\\Users] '
        u'account_rid: 500 '
        u'comments: Built-in account for administering the computer/domain '
        u'login_count: 6 '
        u'user_guid: 000001F4 '
        u'username: Administrator')

    # Match UTC timestamp.
    time = long(timelib_test.CopyStringToTimestamp(
        u'2014-09-24 03:36:06.358837'))
    self.assertEquals(event_object.timestamp, time)

    expected_msg_short = (
        u'[\\SAM\\Domains\\Account\\Users] '
        u'account_rid: 500 '
        u'comments: Built-in account for ...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()

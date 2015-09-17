#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Users key plugin."""

import unittest

from plaso.formatters import winreg as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import sam_users

from tests.parsers.winreg_plugins import test_lib


__author__ = 'Preston Miller, dpmforensics.com, github.com/prmiller91'


class UsersPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the SAM Users key plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = sam_users.UsersPlugin()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath([u'SAM'])
    key_path = u'\\SAM\\Domains\\Account\\Users'
    registry_key = self._GetKeyFromFile(test_file, key_path)
    event_queue_consumer = self._ParseKeyWithPlugin(
        self._plugin, registry_key)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 7)

    event_object = event_objects[0]

    self._TestRegvalue(event_object, u'account_rid', 500)
    self._TestRegvalue(event_object, u'login_count', 6)
    self._TestRegvalue(event_object, u'user_guid', u'000001F4')
    self._TestRegvalue(event_object, u'username', u'Administrator')

    # Match UTC timestamp.
    time = long(timelib.Timestamp.CopyFromString(
        u'2014-09-24 03:36:06.358837'))
    self.assertEqual(event_object.timestamp, time)

    expected_message = (
        u'[\\SAM\\Domains\\Account\\Users] '
        u'account_rid: 500 '
        u'comments: Built-in account for administering the computer/domain '
        u'login_count: 6 '
        u'user_guid: 000001F4 '
        u'username: Administrator')
    expected_short_message = u'{0:s}...'.format(expected_message[0:77])

    self._TestGetMessageStrings(
        event_object, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

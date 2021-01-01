#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS Notification Center plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_notificationcenter

from tests.parsers.sqlite_plugins import test_lib


class MacNotificationCenterTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Notification Center plugin."""

  def testProcess(self):
    """Tests the Process function on a MacOS Notification Center db."""

    plugin = mac_notificationcenter.MacNotificationCenterPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_notificationcenter.db'], plugin)

    self.assertEqual(6, storage_writer.number_of_events)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': 'KeePassXC can now be run',
        'bundle_name': 'com.google.santagui',
        'timestamp': '2018-05-02 10:59:18.930156',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Title: Santa'
        ' '
        'registered by: com.google.santagui. '
        'Presented: Yes, '
        'Content: KeePassXC can now be run')
    expected_short_message = (
        'Title: Santa, '
        'Content: KeePassXC can now be run')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'bundle_name': 'com.google.drivefs',
        'timestamp': '2018-05-02 11:13:21.531085',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Drive File Stream'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_message = (
        'Title: Drive File Stream '
        'registered by: com.google.drivefs. '
        'Presented: Yes, '
        'Content: Drive File Stream is loading your files…')
    expected_short_message = (
        'Title: Drive File Stream, '
        'Content: Drive File Stream is loading your files…')

    event_data = self._GetEventDataOfEvent(storage_writer, events[2])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'body': 'PyCharm can now be run',
        'bundle_name': 'com.google.santagui',
        'timestamp': '2018-05-16 16:38:04.686080',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_message = (
        'Title: Santa '
        'registered by: com.google.santagui. '
        'Presented: Yes, '
        'Content: PyCharm can now be run')
    expected_short_message = (
        'Title: Santa, '
        'Content: PyCharm can now be run')

    event_data = self._GetEventDataOfEvent(storage_writer, events[5])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

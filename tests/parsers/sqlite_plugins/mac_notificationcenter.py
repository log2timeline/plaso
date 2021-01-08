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
        'data_type': 'mac:notificationcenter:db',
        'presented': 1,
        'timestamp': '2018-05-02 10:59:18.930156',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Santa'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'body': 'Drive File Stream is loading your files…',
        'bundle_name': 'com.google.drivefs',
        'data_type': 'mac:notificationcenter:db',
        'presented': 1,
        'timestamp': '2018-05-02 11:13:21.531085',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Drive File Stream'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'body': 'PyCharm can now be run',
        'bundle_name': 'com.google.santagui',
        'data_type': 'mac:notificationcenter:db',
        'presented': 1,
        'timestamp': '2018-05-16 16:38:04.686080',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Santa'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()

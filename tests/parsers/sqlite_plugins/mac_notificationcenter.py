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
    """Tests the Process function."""
    plugin = mac_notificationcenter.MacNotificationCenterPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['mac_notificationcenter.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # TODO: look into rounding differences between date_time and timestamp
    expected_event_values = {
        'body': 'KeePassXC can now be run',
        'bundle_name': 'com.google.santagui',
        'data_type': 'mac:notificationcenter:db',
        'date_time': '2018-05-02T10:59:18.930155+00:00',
        'presented': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Santa'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'body': 'Drive File Stream is loading your files…',
        'bundle_name': 'com.google.drivefs',
        'data_type': 'mac:notificationcenter:db',
        'date_time': '2018-05-02T11:13:21.531085+00:00',
        'presented': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Drive File Stream'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'body': 'PyCharm can now be run',
        'bundle_name': 'com.google.santagui',
        'data_type': 'mac:notificationcenter:db',
        'date_time': '2018-05-16T16:38:04.686079+00:00',
        'presented': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'title': 'Santa'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome notifications database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import chrome_notifications

from tests.parsers.sqlite_plugins import test_lib


class ChromeNotificationsPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome notifications database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome notifications database file."""
    plugin = chrome_notifications.ChromeNotificationsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['chrome_notifications.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'chrome:notification:entry',
        'notification_id': 'notif-id-1',
        'origin': 'https://example.com',
        'service_worker_registration_id': 100,
        'time': '2021-08-25T10:00:00.000000+00:00',
        'title': 'Test Notification',
        'body': 'This is a test',
        'icon': 'icon.png'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'data_type': 'chrome:notification:entry',
        'notification_id': 'notif-id-2',
        'origin': 'https://google.com',
        'service_worker_registration_id': 101,
        'replaced_time': '2021-08-25T10:01:00.000000+00:00',
        'time': '2021-08-25T10:02:00.000000+00:00',
        'title': 'Another Notification',
        'body': 'Hello world',
        'badge': 'badge.png'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

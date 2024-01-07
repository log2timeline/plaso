#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows 10 push notification SQLite database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import windows_push_notification

from tests.parsers.sqlite_plugins import test_lib


class WindowsPushNotificationPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Windows 10 push notification SQLite database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = windows_push_notification.WindowsPushNotificationPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['wpndatabase.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 74)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2020-12-11T19:09:13+00:00',
        'data_type': 'windows:wpndatabase:notification_handler',
        'handler_type': 'app:system',
        'identifier': 'FamilySafety_Settings',
        'modification_time': '2020-12-11T19:09:13+00:00',
        'service_identifier': 'windows.familysafety_cw5n1h2txyewy'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'arrival_time': '2020-12-11T19:11:35.9025799+00:00',
        'boot_time': '2020-12-11T19:08:54.1636157+00:00',
        'data_type': 'windows:wpndatabase:notification',
        'expiration_time': '2020-12-11T19:12:35.9025799+00:00',
        'handler_identifier': (
            'windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.'
            'immersivecontrolpanel'),
        'notification_type': 'toast',
        'payload': (
            '<toast activationType=\'protocol\' '
            'launch=\'ms-settings:connecteddevices\'><visual><binding '
            'template=\'ToastGeneric\'><text id=\'1\'>Setting up a device'
            '</text><text id=\'2\'>We\'re setting up \'PCI Device\'.</text>'
            '</binding></visual></toast>')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 68)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Tango on Android plugins."""

import unittest

from plaso.parsers.sqlite_plugins import android_tango

from tests.parsers.sqlite_plugins import test_lib


class AndroidTangoProfileTest(test_lib.SQLitePluginTestCase):
  """Tests for Tango on Android profile database plugin."""

  def testProcess(self):
    """Test the Process function on a Tango Android file."""
    plugin = android_tango.AndroidTangoProfilePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['tango_android_profile.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 57)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'asccess_time': None,
        'birthday': '1980-10-01',
        'data_type': 'android:tango:contact',
        'distance': 39.04880905,
        'first_name': 'Rouel',
        'friend_request_message': 'I am following you on Tango',
        'friend_request_time': '2016-01-15T14:35:20.436+00:00',
        'friend_request_type': 'outRequest',
        'gender': 'male',
        'is_friend': False,
        'last_active_time': '2016-01-15T13:21:45.624+00:00',
        'last_name': 'Henry',
        'status': 'Praying!'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


class AndroidTangoTCTest(test_lib.SQLitePluginTestCase):
  """Tests for Tango on Android tc databases plugin."""

  def testProcess(self):
    """Test the Process function on a Tango Android file."""
    plugin = android_tango.AndroidTangoTCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['tango_android_tc.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test the a conversation entry.
    expected_event_values = {
        'conversation_identifier': 'DyGWr_010wQM_ozkIe-9Ww',
        'data_type': 'android:tango:conversation'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Test a message creation entry.
    expected_event_values = {
        'data_type': 'android:tango:message',
        'creation_time': '2016-01-15T14:41:33.027+00:00',
        'direction': 2,
        'message_identifier': 16777224,
        'sent_time': '2016-01-15T14:41:34.238+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 14)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

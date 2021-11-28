#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Tango on Android plugins."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import tango_android

from tests.parsers.sqlite_plugins import test_lib


class TangoAndroidProfileTest(test_lib.SQLitePluginTestCase):
  """Tests for Tango on Android profile database plugin."""

  def testProcess(self):
    """Test the Process function on a Tango Android file."""
    plugin = tango_android.TangoAndroidProfilePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['tango_android_profile.db'], plugin)

    # We should have 115 events in total with no warnings.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 115)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test a contact last active event.
    expected_event_values = {
        'birthday': '1980-10-01',
        'data_type': 'tango:android:contact',
        'date_time': '2016-01-15 13:21:45.624',
        'distance': 39.04880905,
        'first_name': 'Rouel',
        'friend_request_message': 'I am following you on Tango',
        'friend_request_type': 'outRequest',
        'gender': 'male',
        'is_friend': False,
        'last_name': 'Henry',
        'status': 'Praying!',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACTIVE}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    # Test a contact last access event.
    expected_event_values = {
        'data_type': 'tango:android:contact',
        'date_time': '2016-01-15 14:35:20.633',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[57], expected_event_values)

    # Test a contact request sent event.
    expected_event_values = {
        'data_type': 'tango:android:contact',
        'date_time': '2016-01-15 14:35:20.436',
        'timestamp_desc': definitions.TIME_DESCRIPTION_SENT}

    self.CheckEventValues(storage_writer, events[56], expected_event_values)


class TangoAndroidTCTest(test_lib.SQLitePluginTestCase):
  """Tests for Tango on Android tc databases plugin."""

  def testProcess(self):
    """Test the Process function on a Tango Android file."""
    plugin = tango_android.TangoAndroidTCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['tango_android_tc.db'], plugin)

    # We should have 43 events in total with no warnings.
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 43)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Test the a conversation event.
    expected_event_values = {
        'conversation_identifier': 'DyGWr_010wQM_ozkIe-9Ww',
        'data_type': 'tango:android:conversation',
        'date_time': 'Not set',
        'timestamp_desc': definitions.TIME_DESCRIPTION_NOT_A_TIME}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Test a message creation event.
    expected_event_values = {
        'data_type': 'tango:android:message',
        'date_time': '2016-01-15 14:41:33.027',
        'direction': 2,
        'message_identifier': 16777224,
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)

    # Test a message sent event.
    expected_event_values = {
        'data_type': 'tango:android:message',
        'date_time': '2016-01-15 14:41:34.238',
        'direction': 2,
        'message_identifier': 16777224,
        'timestamp_desc': definitions.TIME_DESCRIPTION_SENT}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)


if __name__ == '__main__':
  unittest.main()

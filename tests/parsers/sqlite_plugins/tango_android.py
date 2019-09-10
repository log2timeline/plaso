#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Tango on Android plugins."""

from __future__ import unicode_literals

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

    # We should have 115 tango profile events in total with no warnings.
    self.assertEqual(115, storage_writer.number_of_events)
    self.assertEqual(0, storage_writer.number_of_warnings)

    events = list(storage_writer.GetSortedEvents())

    # Test tango contact last active time event.
    event = events[14]

    self.CheckTimestamp(event.timestamp, '2016-01-15 13:21:45.624000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACTIVE)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.first_name, 'Rouel')
    self.assertEqual(event_data.last_name, 'Henry')
    self.assertEqual(event_data.birthday, '1980-10-01')
    self.assertEqual(event_data.gender, 'male')
    self.assertEqual(event_data.status, 'Praying!')
    self.assertEqual(event_data.distance, 39.04880905)
    self.assertEqual(event_data.is_friend, False)
    self.assertEqual(event_data.friend_request_type, 'outRequest')
    self.assertEqual(
        event_data.friend_request_message, 'I am following you on Tango')

    expected_message = (
        'Rouel Henry male birthday: 1980-10-01 Status: Praying! Friend: False '
        'Request type: outRequest Request message: I am following you on Tango'
    )

    expected_short_message = 'Rouel Henry Status: Praying!'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test tango contact last access time event.
    event = events[57]

    self.CheckTimestamp(event.timestamp, '2016-01-15 14:35:20.633000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    # Test tango contact request sent time event.
    event = events[56]

    self.CheckTimestamp(event.timestamp, '2016-01-15 14:35:20.436000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_SENT)


class TangoAndroidTCTest(test_lib.SQLitePluginTestCase):
  """Tests for Tango on Android tc databases plugin."""

  def testProcess(self):
    """Test the Process function on a Tango Android file."""
    plugin = tango_android.TangoAndroidTCPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['tango_android_tc.db'], plugin)

    # We should have 43 tango tc events in total with no warnings.
    self.assertEqual(43, storage_writer.number_of_events)
    self.assertEqual(0, storage_writer.number_of_warnings)

    events = list(storage_writer.GetSortedEvents())

    # Test the first tango conversation event.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '1970-01-01 00:00:00.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_NOT_A_TIME)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.conversation_identifier, 'DyGWr_010wQM_ozkIe-9Ww')

    expected_message = 'Conversation (DyGWr_010wQM_ozkIe-9Ww)'
    expected_short_message = 'Conversation (DyGWr_010wQM_ozkIe-9Ww)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test tango message creation time event
    event = events[21]

    self.CheckTimestamp(event.timestamp, '2016-01-15 14:41:33.027000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.message_identifier, 16777224)
    self.assertEqual(event_data.direction, 2)

    expected_message = 'Outgoing Message (16777224)'
    expected_short_message = 'Outgoing Message (16777224)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Test tango message sent time event
    event = events[22]

    self.CheckTimestamp(event.timestamp, '2016-01-15 14:41:34.238000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_SENT)


if __name__ == '__main__':
  unittest.main()

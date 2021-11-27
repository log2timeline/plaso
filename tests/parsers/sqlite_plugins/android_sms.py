#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android SMS plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import android_sms

from tests.parsers.sqlite_plugins import test_lib


class AndroidSMSTest(test_lib.SQLitePluginTestCase):
  """Tests for the Android SMS database plugin."""

  def testProcess(self):
    """Test the Process function on an Android SMS mmssms.db file."""
    plugin = android_sms.AndroidSMSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['mmssms.db'], plugin)

    # The SMS database file contains 9 events (5 SENT, 4 RECEIVED messages).
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    # Check the first SMS sent.
    expected_event_values = {
        'address': '1 555-521-5554',
        'body': 'Yo Fred this is my new number.',
        'data_type': 'android:messaging:sms',
        'date_time': '2013-10-29 16:56:28.038',
        'sms_type': 'SENT',
        'sms_read': 'READ',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()

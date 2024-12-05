#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Call Screen history plugin."""

import unittest

from plaso.parsers.sqlite_plugins import android_google_callscreen

from tests.parsers.sqlite_plugins import test_lib


class AndroidGoogleCallScreenSQLitePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Call Screen database plugin."""

  def testProcess(self):
    """Test the Process function on an Android callscreen_transcripts file."""
    plugin = android_google_callscreen.GoogleCallScreenPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['callscreen_transcripts'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 31)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'android:google:callscreen',
        'file_path': '/data/user/0/com.google.android.dialer/files/callscreenrecordings/cs-1663338171971.m4a',
        'timestamp': '2022-09-16T14:23:03.767+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

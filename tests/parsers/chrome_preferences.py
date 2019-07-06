#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome Preferences file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_preferences as _  # pylint: disable=unused-import
from plaso.parsers import chrome_preferences

from tests.parsers import test_lib


class ChromePreferencesParserTest(test_lib.ParserTestCase):
  """Tests for the Google Chrome Preferences file parser."""

  def testParseFile(self):
    """Tests parsing a default profile Preferences file."""
    parser = chrome_preferences.ChromePreferencesParser()
    storage_writer = self._ParseFile(['Preferences'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 30)

    events = list(storage_writer.GetSortedEvents())

    event = events[17]

    self.CheckTimestamp(event.timestamp, '2014-11-12 13:01:43.926143')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Chrome extensions autoupdater last run'
    expected_short_message = 'Chrome extensions autoupdater last run'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[18]

    self.CheckTimestamp(event.timestamp, '2014-11-12 18:20:21.519200')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Chrome extensions autoupdater next run'
    expected_short_message = 'Chrome extensions autoupdater next run'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[22]

    self.CheckTimestamp(event.timestamp, '2016-06-08 16:17:47.453766')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Chrome history was cleared by user'
    expected_short_message = 'Chrome history was cleared by user'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2014-11-05 18:31:24.154837')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.data_type, 'chrome:preferences:extension_installation')
    self.assertEqual(
        event_data.extension_id, 'mgndgikekgjfcpckkfioiadnlibdjbkf')
    self.assertEqual(event_data.extension_name, 'Chrome')

    expected_path = (
        'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
        'resources\\chrome_app')
    self.assertEqual(event_data.path, expected_path)

    expected_message = (
        'CRX ID: mgndgikekgjfcpckkfioiadnlibdjbkf '
        'CRX Name: Chrome '
        'Path: {0:s}'.format(expected_path))
    expected_short_message = (
        'mgndgikekgjfcpckkfioiadnlibdjbkf '
        'C:\\Program Files\\Google\\Chrome\\Application\\3...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[25]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:50.588974')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Permission geolocation used by local file'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[23]

    self.CheckTimestamp(event.timestamp, '2016-11-11 16:20:09.866137')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Permission midi_sysex used by https://rawgit.com:443')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[29]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:13:00.639332')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')
    expected_short_message = (
        'Permission notifications used by https://rawgit.com:443')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[28]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:13:00.627093')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[27]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:54.899474')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Permission media_stream_mic used by local file')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)

    event = events[26]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:53.667838')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Permission media_stream_mic used by https://rawgit.com:443')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

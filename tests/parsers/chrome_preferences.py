#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome Preferences file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_preferences as _  # pylint: disable=unused-import
from plaso.parsers import chrome_preferences

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ChromePreferencesParserTest(test_lib.ParserTestCase):
  """Tests for the Google Chrome Preferences file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['Preferences'])
  def testParseFile(self):
    """Tests parsing a default profile Preferences file."""
    parser = chrome_preferences.ChromePreferencesParser()
    storage_writer = self._ParseFile(['Preferences'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 30)

    events = list(storage_writer.GetSortedEvents())

    event = events[17]

    self.CheckTimestamp(event.timestamp, '2014-11-12 13:01:43.926143')

    expected_message = 'Chrome extensions autoupdater last run'
    expected_short_message = 'Chrome extensions autoupdater last run'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[18]

    self.CheckTimestamp(event.timestamp, '2014-11-12 18:20:21.519200')

    expected_message = 'Chrome extensions autoupdater next run'
    expected_short_message = 'Chrome extensions autoupdater next run'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[22]

    self.CheckTimestamp(event.timestamp, '2016-06-08 16:17:47.453766')

    expected_message = 'Chrome history was cleared by user'
    expected_short_message = 'Chrome history was cleared by user'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[6]

    self.assertEqual(
        event.data_type, 'chrome:preferences:extension_installation')

    self.CheckTimestamp(event.timestamp, '2014-11-05 18:31:24.154837')

    expected_id = 'mgndgikekgjfcpckkfioiadnlibdjbkf'
    self.assertEqual(event.extension_id, expected_id)

    expected_name = 'Chrome'
    self.assertEqual(event.extension_name, expected_name)

    expected_path = (
        'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
        'resources\\chrome_app')
    self.assertEqual(event.path, expected_path)

    expected_message = (
        'CRX ID: {0:s} CRX Name: {1:s} Path: {2:s}'.format(
            expected_id, expected_name, expected_path))
    expected_short_message = (
        '{0:s} '
        'C:\\Program Files\\Google\\Chrome\\Application\\3...').format(
            expected_id)
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[25]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:50.588974')

    expected_message = 'Permission geolocation used by local file'
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[23]

    self.CheckTimestamp(event.timestamp, '2016-11-11 16:20:09.866137')

    expected_message = (
        'Permission midi_sysex used by https://rawgit.com:443')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[29]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:13:00.639332')

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')
    expected_short_message = (
        'Permission notifications used by https://rawgit.com:443')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    event = events[28]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:13:00.627093')

    expected_message = (
        'Permission notifications used by https://rawgit.com:443')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[27]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:54.899474')

    expected_message = (
        'Permission media_stream_mic used by local file')
    self._TestGetMessageStrings(event, expected_message, expected_message)

    event = events[26]

    self.CheckTimestamp(event.timestamp, '2016-11-14 14:12:53.667838')

    expected_message = (
        'Permission media_stream_mic used by https://rawgit.com:443')
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

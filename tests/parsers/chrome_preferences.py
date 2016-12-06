#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Chrome Preferences file parser."""

import unittest

from plaso.formatters import chrome_preferences  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import chrome_preferences

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ChromePreferencesParserTest(test_lib.ParserTestCase):
  """Tests for the Google Chrome Preferences file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'Preferences'])
  def testParseFile(self):
    """Tests parsing a default profile Preferences file."""
    parser_object = chrome_preferences.ChromePreferencesParser()
    storage_writer = self._ParseFile(
        [u'Preferences'], parser_object)

    self.assertEqual(len(storage_writer.events), 28)

    event = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-12 13:01:43.926143')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (u'Chrome extensions autoupdater last run')
    expected_message_short = (u'Chrome extensions autoupdater last run')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-12 18:20:21.519200')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (u'Chrome extensions autoupdater next run')
    expected_message_short = (u'Chrome extensions autoupdater next run')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[2]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-06-08 16:17:47.453766')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (u'Chrome history was cleared by user')
    expected_message_short = (u'Chrome history was cleared by user')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[17]

    self.assertIsInstance(
        event, chrome_preferences.ChromeExtensionInstallationEvent)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-05 18:31:24.154837')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_id = u'mgndgikekgjfcpckkfioiadnlibdjbkf'
    self.assertEqual(event.extension_id, expected_id)

    expected_name = u'Chrome'
    self.assertEqual(event.extension_name, expected_name)

    expected_path = (
        u'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
        u'resources\\chrome_app')
    self.assertEqual(event.path, expected_path)

    expected_message = (
        u'CRX ID: {0:s} CRX Name: {1:s} Path: {2:s}'.format(
            expected_id, expected_name, expected_path))
    expected_message_short = (
        u'{0:s} '
        u'C:\\Program Files\\Google\\Chrome\\Application\\3...').format(
            expected_id)
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)


    event = storage_writer.events[22]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-14 14:12:50.588973')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (u'Permission geolocation used by a local file')
    self._TestGetMessageStrings(
        event, expected_message, expected_message)

    event = storage_writer.events[23]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-11 16:20:09.866137')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (
        u'Permission midi_sysex used by https://rawgit.com:443')
    expected_message_short = expected_message
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[24]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-14 14:13:00.639332')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (
        u'Permission notifications used by https://rawgit.com:443')
    expected_message_short = (
        u'Permission notifications used by https://rawgit.com:443')
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[25]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-14 14:13:00.627093')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (
        u'Permission notifications used by https://rawgit.com:443')
    expected_message_short = expected_message
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[26]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-14 14:12:54.899473')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (
        u'Permission media_stream_mic used by a local file')
    expected_message_short = expected_message
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)

    event = storage_writer.events[27]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-11-14 14:12:53.667838')
    self.assertEqual(event.timestamp, expected_timestamp)
    expected_message = (
        u'Permission media_stream_mic used by https://rawgit.com:443')
    expected_message_short = expected_message
    self._TestGetMessageStrings(
        event, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()

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

    self.assertEqual(len(storage_writer.events), 20)

    event_object = storage_writer.events[14]

    self.assertIsInstance(
        event_object, chrome_preferences.ChromeExtensionInstallationEvent)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-05 18:31:24.154837')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_id = u'mgndgikekgjfcpckkfioiadnlibdjbkf'
    self.assertEqual(event_object.extension_id, expected_id)

    expected_name = u'Chrome'
    self.assertEqual(event_object.extension_name, expected_name)

    expected_path = (
        u'C:\\Program Files\\Google\\Chrome\\Application\\38.0.2125.111\\'
        u'resources\\chrome_app')
    self.assertEqual(event_object.path, expected_path)

    expected_message = (
        u'CRX ID: {0:s} CRX Name: {1:s} Path: {2:s}'.format(
            expected_id, expected_name, expected_path))
    expected_message_short = (
        u'{0:s} '
        u'C:\\Program Files\\Google\\Chrome\\Application\\3...').format(
            expected_id)
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()

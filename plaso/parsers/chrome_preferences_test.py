#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Chrome Preferences file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import chrome_preferences as chrome_preferences_formatter
from plaso.lib import timelib
from plaso.parsers import test_lib
from plaso.parsers import chrome_preferences


class ChromePreferencesParserTest(test_lib.ParserTestCase):
  """Tests for the Google Chrome Preferences file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = chrome_preferences.ChromePreferencesParser()

  def testParseFile(self):
    """Tests parsing a default profile Preferences file."""
    test_file = self._GetTestFilePath([u'Preferences'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # event_object[0] from the sample is mgndgikekgjfcpckkfioiadnlibdjbkf
    event_object = event_objects[0]

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

    expected_msg = (
        u'CRX ID: {0:s} CRX Name: {1:s} Path: {2:s}'.format(
            expected_id, expected_name, expected_path))
    expected_short_path = (
        u'C:\\Program Files\\Google\\Chrome\\Application\\3...')
    expected_short = (u'{0:s} {1:s}'.format(expected_id, expected_short_path))
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()

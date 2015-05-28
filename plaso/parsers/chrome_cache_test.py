#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Chrome Cache files parser."""

import unittest

from plaso.formatters import chrome_cache as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import test_lib
from plaso.parsers import chrome_cache


class ChromeCacheParserTest(test_lib.ParserTestCase):
  """Tests for the Chrome Cache files parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = chrome_cache.ChromeCacheParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'chrome_cache', u'index'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 217)

    event_object = event_objects[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-04-30 16:44:36.226091')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_original_url = (
        u'https://s.ytimg.com/yts/imgbin/player-common-vfliLfqPT.webp')
    self.assertEqual(event_object.original_url, expected_original_url)

    expected_string = u'Original URL: {0:s}'.format(expected_original_url)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()

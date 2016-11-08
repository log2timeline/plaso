#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Chrome Cache files parser."""

import unittest

from plaso.formatters import chrome_cache  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import chrome_cache

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ChromeCacheParserTest(test_lib.ParserTestCase):
  """Tests for the Chrome Cache files parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'chrome_cache', u'index'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = chrome_cache.ChromeCacheParser()
    storage_writer = self._ParseFile(
        [u'chrome_cache', u'index'], parser_object)

    self.assertEqual(len(storage_writer.events), 217)

    event_object = storage_writer.events[0]

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

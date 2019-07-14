#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome Cache files parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_cache as _  # pylint: disable=unused-import
from plaso.parsers import chrome_cache

from tests.parsers import test_lib


class ChromeCacheParserTest(test_lib.ParserTestCase):
  """Tests for the Chrome Cache files parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = chrome_cache.ChromeCacheParser()
    storage_writer = self._ParseFile(['chrome_cache', 'index'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 217)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-04-30 16:44:36.226091')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_original_url = (
        'https://s.ytimg.com/yts/imgbin/player-common-vfliLfqPT.webp')
    self.assertEqual(event_data.original_url, expected_original_url)

    expected_message = 'Original URL: {0:s}'.format(expected_original_url)

    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

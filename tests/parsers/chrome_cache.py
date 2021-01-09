#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Chrome Cache files parser."""

import unittest

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

    expected_original_url = (
        'https://s.ytimg.com/yts/imgbin/player-common-vfliLfqPT.webp')

    expected_event_values = {
        'timestamp': '2014-04-30 16:44:36.226091',
        'original_url': expected_original_url}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = 'Original URL: {0:s}'.format(expected_original_url)

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

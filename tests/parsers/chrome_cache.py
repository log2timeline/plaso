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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 217)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2014-04-30T16:44:36.226091+00:00',
        'data_type': 'chrome:cache:entry',
        'original_url': (
            'https://s.ytimg.com/yts/imgbin/player-common-vfliLfqPT.webp')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

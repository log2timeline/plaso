#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Amcache Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import amcache

from tests.parsers import test_lib


class AmcacheParserTest(test_lib.ParserTestCase):
  """Tests for the Amcache Registry plugin."""

  def testParse(self):
    """Tests the Parse function."""
    parser = amcache.AmcacheParser()

    storage_writer = self._ParseFile(['Amcache.hve'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1179)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '1992-06-19 22:22:17.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')
    self.assertEqual(event_data.full_path, expected_full_path)

    expected_sha1 = '82274eef0911a948f91425f5e5b0e730517fe75e'
    self.assertEqual(event_data.sha1, expected_sha1)

    event = events[1148]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_program_name = 'FileInsight - File analysis tool'
    self.assertEqual(event_data.name, expected_program_name)

    expected_publisher = 'McAfee Inc.'
    self.assertEqual(event_data.publisher, expected_publisher)

    # TODO: add test for message string

  def testParseWithSystem(self):
    """Tests the Parse function with a SYSTEM Registry file."""
    parser = amcache.AmcacheParser()

    storage_writer = self._ParseFile(['SYSTEM'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 0)


if __name__ == '__main__':
  unittest.main()

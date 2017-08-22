#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Amcache Registry plugin."""

from __future__ import unicode_literals
import unittest

from plaso.lib import timelib
from tests import test_lib as shared_test_lib
from tests.parsers import test_lib
from plaso.parsers import amcache

__author__ = 'Ramses de Beer, rbdebeer@google.com'

class AmcacheParserTest(test_lib.ParserTestCase):
  """Tests for the Amcache Registry plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['Amcache.hve'])
  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testParse(self):
    """Tests the Parse function."""
    parser = amcache.AmcacheParser()

    storage_writer = self._ParseFile(['SYSTEM'], parser)

    self.assertEqual(storage_writer.number_of_events, 0)

    storage_writer = self._ParseFile(['Amcache.hve'], parser)

    self.assertEqual(storage_writer.number_of_events, 1179)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '1992-06-19 22:22:17.000000')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')
    self.assertEqual(event.full_path, expected_full_path)

    expected_sha1 = '82274eef0911a948f91425f5e5b0e730517fe75e'
    self.assertEqual(event.sha1, expected_sha1)

    event = events[1148]

    expected_program_name = ('FileInsight - File analysis tool')
    self.assertEqual(event.name, expected_program_name)

    expected_publisher = ('McAfee Inc.')
    self.assertEqual(event.publisher, expected_publisher)

if __name__ == '__main__':
  unittest.main()

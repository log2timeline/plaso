# -*- coding: utf-8 -*-
"""Tests for fseventsd file parser."""

from __future__ import unicode_literals
import unittest

from plaso.lib import timelib
from tests import test_lib as shared_test_lib
from tests.parsers import test_lib
from plaso.parsers import fseventsd


class FSEventsdParserTest(test_lib.ParserTestCase):


  @shared_test_lib.skipUnlessHasTestFile(
      ['fsevents-0000000002d89b58-decompressed'])
  def testParse(self):
    """Tests the Parse function."""
    parser = fseventsd.FSEventsdParser()

    storage_writer = self._ParseFile(
        ['fsevents-0000000002d89b58-decompressed'], parser)

    self.assertEqual(storage_writer.number_of_events, 12)

    events = list(storage_writer.GetEvents())

    event = events[3]
    self.assertEqual(event.path, '.Spotlight-V100/Store-V1')
    self.assertEqual(event.event_id, 47747061)
    self.assertEqual(event.flags, b'\x00\x00\x00\x00\x80\x00\x00\x01')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2017-10-18 11:55:20')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = storage_writer.events[0]
    self.assertEqual(event.filename, None)

    self.assertNotEquals(storage_writer.number_of_events, 0)


if __name__ == '__main__':
  unittest.main()

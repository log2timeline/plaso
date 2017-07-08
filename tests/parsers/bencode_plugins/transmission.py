#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

import unittest

from plaso.formatters import bencode_parser  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import bencode_parser

from tests import test_lib as shared_test_lib
from tests.parsers.bencode_plugins import test_lib


class BencodeTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for Transmission BitTorrent files."""

  @shared_test_lib.skipUnlessHasTestFile([u'bencode_transmission'])
  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile([u'bencode_transmission'], parser)

    self.assertEqual(storage_writer.number_of_events, 3)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_destination = u'/Users/brian/Downloads'
    self.assertEqual(event.destination, expected_destination)

    self.assertEqual(event.seedtime, 4)

    expected_description = definitions.TIME_DESCRIPTION_ADDED
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 15:31:20')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test on second event of first torrent.
    event = events[1]
    self.assertEqual(event.destination, expected_destination)
    self.assertEqual(event.seedtime, 4)

    expected_description = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 18:24:24')
    self.assertEqual(event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()

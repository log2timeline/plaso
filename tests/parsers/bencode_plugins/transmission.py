#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import bencode_parser as bencode_formatter
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class BencodeTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for Transmission BitTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser_object = bencode_parser.BencodeParser()

    storage_writer = self._ParseFile(
        [u'bencode_transmission'], parser_object)

    self.assertEqual(len(storage_writer.events), 3)

    event_object = storage_writer.events[0]

    expected_destination = u'/Users/brian/Downloads'
    self.assertEqual(event_object.destination, expected_destination)

    self.assertEqual(event_object.seedtime, 4)

    expected_description = eventdata.EventTimestamp.ADDED_TIME
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 15:31:20')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test on second event of first torrent.
    event_object = storage_writer.events[1]
    self.assertEqual(event_object.destination, expected_destination)
    self.assertEqual(event_object.seedtime, 4)

    expected_description = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, expected_description)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 18:24:24')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()

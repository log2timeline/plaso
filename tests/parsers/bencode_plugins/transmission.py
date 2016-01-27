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

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = bencode_parser.BencodeParser()

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath([u'bencode_transmission'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 3)

    event_object = event_objects[0]

    destination_expected = u'/Users/brian/Downloads'
    self.assertEqual(event_object.destination, destination_expected)

    self.assertEqual(event_object.seedtime, 4)

    description_expected = eventdata.EventTimestamp.ADDED_TIME
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 15:31:20')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Test on second event of first torrent.
    event_object = event_objects[1]
    self.assertEqual(event_object.destination, destination_expected)
    self.assertEqual(event_object.seedtime, 4)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-08 18:24:24')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()

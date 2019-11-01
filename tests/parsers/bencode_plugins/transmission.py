#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import bencode_parser as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class BencodeTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for Transmission BitTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile(['bencode_transmission'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-11-08 15:31:20.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.destination, '/Users/brian/Downloads')
    self.assertEqual(event_data.seedtime, 4)

    # Test on second event of first torrent.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-11-08 18:24:24.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.destination, '/Users/brian/Downloads')
    self.assertEqual(event_data.seedtime, 4)

    expected_message = (
        'Saved to /Users/brian/Downloads; '
        'Minutes seeded: 4')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

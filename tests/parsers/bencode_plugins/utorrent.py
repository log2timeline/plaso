#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for uTorrent files."""

from __future__ import unicode_literals

import unittest

# pylint: disable=unused-import
from plaso.formatters import bencode_parser as _
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class UTorrentPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for uTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile(['bencode_utorrent'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # First test on when the torrent was added to the client.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-08-03 14:52:12.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.caption, 'plaso test')
    self.assertEqual(event_data.path, 'e:\\torrent\\files\\plaso test')
    self.assertEqual(event_data.seedtime, 511)

    # Second test on when the torrent file was completely downloaded.
    event = events[3]

    self.CheckTimestamp(event.timestamp, '2013-08-03 18:11:35.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.caption, 'plaso test')
    self.assertEqual(event_data.path, 'e:\\torrent\\files\\plaso test')
    self.assertEqual(event_data.seedtime, 511)

    # Third test on when the torrent was first modified.
    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-08-03 18:11:34.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.caption, 'plaso test')
    self.assertEqual(event_data.path, 'e:\\torrent\\files\\plaso test')
    self.assertEqual(event_data.seedtime, 511)

    # Fourth test on when the torrent was again modified.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-08-03 16:27:59.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.caption, 'plaso test')
    self.assertEqual(event_data.path, 'e:\\torrent\\files\\plaso test')
    self.assertEqual(event_data.seedtime, 511)

    expected_message = (
        'Torrent plaso test; Saved to e:\\torrent\\files\\plaso test; '
        'Minutes seeded: 511')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for uTorrent files."""

import unittest

from plaso.lib import definitions
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class UTorrentPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for uTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile(['bencode', 'utorrent'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    # First test on when the torrent was added to the client.
    expected_event_values = {
        'caption': 'plaso test',
        'data_type': 'p2p:bittorrent:utorrent',
        'date_time': '2013-08-03 14:52:12',
        'path': 'e:\\torrent\\files\\plaso test',
        'seedtime': 511,
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Second test on when the torrent file was completely downloaded.
    expected_event_values = {
        'caption': 'plaso test',
        'data_type': 'p2p:bittorrent:utorrent',
        'date_time': '2013-08-03 18:11:35',
        'path': 'e:\\torrent\\files\\plaso test',
        'seedtime': 511,
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    # Third test on when the torrent was first modified.
    expected_event_values = {
        'caption': 'plaso test',
        'data_type': 'p2p:bittorrent:utorrent',
        'date_time': '2013-08-03 18:11:34',
        'path': 'e:\\torrent\\files\\plaso test',
        'seedtime': 511,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    # Fourth test on when the torrent was again modified.
    expected_event_values = {
        'caption': 'plaso test',
        'data_type': 'p2p:bittorrent:utorrent',
        'date_time': '2013-08-03 16:27:59',
        'path': 'e:\\torrent\\files\\plaso test',
        'seedtime': 511,
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()

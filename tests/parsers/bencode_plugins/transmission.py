#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

import unittest

from plaso.lib import definitions
from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class TransmissionPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for Transmission BitTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile(['bencode', 'transmission'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which BencodeParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'p2p:bittorrent:transmission',
        'date_time': '2013-11-08 15:31:20',
        'destination': '/Users/brian/Downloads',
        'seedtime': 4,
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Test on second event of first torrent.
    expected_event_values = {
        'data_type': 'p2p:bittorrent:transmission',
        'date_time': '2013-11-08 18:24:24',
        'destination': '/Users/brian/Downloads',
        'seedtime': 4,
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the bencode parser plugin for Transmission BitTorrent files."""

import unittest

from plaso.parsers import bencode_parser

from tests.parsers.bencode_plugins import test_lib


class TransmissionPluginTest(test_lib.BencodePluginTestCase):
  """Tests for bencode parser plugin for Transmission BitTorrent files."""

  def testProcess(self):
    """Tests the Process function."""
    parser = bencode_parser.BencodeParser()
    storage_writer = self._ParseFile(['bencode', 'transmission'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2013-11-08T15:31:20+00:00',
        'data_type': 'p2p:bittorrent:transmission',
        'destination': '/Users/brian/Downloads',
        'downloaded_time': '2013-11-08T18:24:24+00:00',
        'seedtime': 4}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

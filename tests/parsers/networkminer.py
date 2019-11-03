#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the NetworkMiner fileinfos parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import networkminer

from tests.parsers import test_lib


class NetworkMinerUnitTest(test_lib.ParserTestCase):
  """Tests for the NetworkMiner fileinfos parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = networkminer.NetworkMinerParser()
    storage_writer = self._ParseFile(
        ['networkminer.pcap.FileInfos.csv'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())
    event = events[3]

    self.CheckTimestamp(event.timestamp, '2007-12-17 04:32:30.399052')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.source_ip, '111.123.124.11')
    self.assertEqual(event_data.filename, 'index.html')

    expected_message = (
        'Source IP: 111.123.124.11 '
        'Source Port: TCP 80 '
        'Destination IP: 192.168.151.130 '
        'Destination Port: TCP 48304 '
        'index.html D:\\case-export\\AssembledFiles\\index.html '
        '98 500 B '
        'abdb151dfd5775c05b47c0f4ea1cd3d7 '
        'travelocity.com/')

    short_message = (
        'Source IP: 111.123.124.11 '
        'Destination IP: 192.168.151.130 '
        'index.html D:\\case-...')
    self._TestGetMessageStrings(event_data, expected_message, short_message)

if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the NetworkMiner fileinfos parser."""

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'networkminer:fileinfos:file',
        'date_time': '2007-12-17 04:32:30.399052',
        'destination_ip': '192.168.151.130',
        'destination_port': 'TCP 48304',
        'file_details': 'travelocity.com/',
        'file_md5': 'abdb151dfd5775c05b47c0f4ea1cd3d7',
        'file_size': '98 500 B',
        'file_path': 'D:\\case-export\\AssembledFiles\\index.html',
        'filename': 'index.html',
        'source_ip': '111.123.124.11',
        'source_port': 'TCP 80'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)


if __name__ == '__main__':
  unittest.main()

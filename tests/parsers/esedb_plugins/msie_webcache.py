#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

from plaso.lib import definitions
from plaso.parsers.esedb_plugins import msie_webcache

from tests.parsers.esedb_plugins import test_lib


class MsieWebCacheESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the MSIE WebCache ESE database plugin."""

  # pylint: disable=protected-access

  def testConvertHeadersValues(self):
    """Tests the _ConvertHeadersValues function."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()

    binary_value = (
        b'HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n'
        b'X-Content-Type-Options: nosniff\r\nContent-Length: 2759\r\n'
        b'X-XSS-Protection: 1; mode=block\r\n'
        b'Alternate-Protocol: 80:quic\r\n\r\n')

    expected_headers_value = (
        '[HTTP/1.1 200 OK; Content-Type: image/png; '
        'X-Content-Type-Options: nosniff; Content-Length: 2759; '
        'X-XSS-Protection: 1; mode=block; '
        'Alternate-Protocol: 80:quic]')

    headers_value = plugin._ConvertHeadersValues(binary_value)
    self.assertEqual(headers_value, expected_headers_value)

  def testProcessOnDatabaseWithPartitionsTable(self):
    """Tests the Process function on database with a Partitions table."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(['WebCacheV01.dat'], plugin)

    self.assertEqual(storage_writer.number_of_events, 1372)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'container_identifier': 1,
        'data_type': 'msie:webcache:containers',
        'date_time': '2014-05-12 07:30:25.4861987',
        'directory': (
            'C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
            'INetCache\\IE\\'),
        'name': 'Content',
        'set_identifier': 0,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[573], expected_event_values)

  def testProcessOnDatabaseWithPartitionsExTable(self):
    """Tests the Process function on database with a PartitionsEx table."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['PartitionsEx-WebCacheV01.dat'], plugin)

    self.assertEqual(storage_writer.number_of_events, 4200)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 3)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'access_count': 5,
        'cache_identifier': 0,
        'cached_file_size': 726,
        'cached_filename': 'b83d57c0[1].svg',
        'container_identifier': 14,
        'data_type': 'msie:webcache:container',
        'date_time': '2019-03-20 17:22:14.0000000',
        'entry_identifier': 63,
        'sync_count': 0,
        'response_headers': (
            '[HTTP/1.1 200; content-length: 726; content-type: image/svg+xml; '
            'x-cache: TCP_HIT; x-msedge-ref: Ref A: 3CD5FCBC8EAD4E0A80FA41A62'
            'FBC8CCC Ref B: PRAEDGE0910 Ref C: 2019-12-16T20:55:28Z; date: '
            'Mon, 16 Dec 2019 20:55:28 GMT]'),
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION,
        'url': 'https://www.bing.com/rs/3R/kD/ic/878ca0cd/b83d57c0.svg'}

    self.CheckEventValues(storage_writer, events[100], expected_event_values)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msie_webcache as _  # pylint: disable=unused-import
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
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['WebCacheV01.dat'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1354)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[567]

    self.CheckTimestamp(event.timestamp, '2014-05-12 07:30:25.486199')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.container_identifier, 1)

    expected_message = (
        'Name: Content '
        'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        'INetCache\\IE\\ '
        'Table: Container_1 '
        'Container identifier: 1 '
        'Set identifier: 0')
    expected_short_message = (
        'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        'INetCache\\IE\\')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testProcessOnDatabaseWithPartitionsExTable(self):
    """Tests the Process function on database with a PartitionsEx table."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['PartitionsEx-WebCacheV01.dat'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 3)
    self.assertEqual(storage_writer.number_of_events, 4014)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[100]

    self.CheckTimestamp(event.timestamp, '2019-03-20 17:22:14.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.container_identifier, 14)

    expected_message = (
        'URL: https://www.bing.com/rs/3R/kD/ic/878ca0cd/b83d57c0.svg '
        'Access count: 5 '
        'Sync count: 0 '
        'Filename: b83d57c0[1].svg '
        'Cached file size: 726 '
        'Response headers: [HTTP/1.1 200; '
        'content-length: 726; '
        'content-type: image/svg+xml; '
        'x-cache: TCP_HIT; '
        'x-msedge-ref: Ref A: 3CD5FCBC8EAD4E0A80FA41A62FBC8CCC '
        'Ref B: PRAEDGE0910 Ref C: 2019-12-16T20:55:28Z; '
        'date: Mon, 16 Dec 2019 20:55:28 GMT] '
        'Entry identifier: 63 Container identifier: 14 Cache identifier: 0')
    expected_short_message = (
        'URL: https://www.bing.com/rs/3R/kD/ic/878ca0cd/b83d57c0.svg')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()

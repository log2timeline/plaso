#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

import unittest

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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 341)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2014-05-12T07:30:25.4861987+00:00',
        'container_identifier': 1,
        'data_type': 'msie:webcache:containers',
        'directory': (
            'C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
            'INetCache\\IE\\'),
        'name': 'Content',
        'set_identifier': 0}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessOnDatabaseWithPartitionsExTable(self):
    """Tests the Process function on database with a PartitionsEx table."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['PartitionsEx-WebCacheV01.dat'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1143)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_count': 5,
        'cache_identifier': 0,
        'cached_file_size': 726,
        'cached_filename': 'b83d57c0[1].svg',
        'container_identifier': 14,
        'data_type': 'msie:webcache:container',
        'entry_identifier': 63,
        'modification_time': '2019-03-20T17:22:14.0000000+00:00',
        'response_headers': (
            '[HTTP/1.1 200; content-length: 726; content-type: image/svg+xml; '
            'x-cache: TCP_HIT; x-msedge-ref: Ref A: 3CD5FCBC8EAD4E0A80FA41A62'
            'FBC8CCC Ref B: PRAEDGE0910 Ref C: 2019-12-16T20:55:28Z; date: '
            'Mon, 16 Dec 2019 20:55:28 GMT]'),
        'synchronization_count': 0,
        'url': 'https://www.bing.com/rs/3R/kD/ic/878ca0cd/b83d57c0.svg'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 211)
    self.CheckEventData(event_data, expected_event_values)

  def testProcessOnDatabaseWithCookiesExTable(self):
    """Tests the Process function on database with a CookiesEx table."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['WebCacheV01_cookies.dat'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 276)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
            'cookie_hash': '5b4342ed6e2b0ae16f7e2c4c',
            'cookie_name': 'abid',
            'cookie_value': 'fcc450d1-8674-1bd3-4074-a240cff5c5b1',
            'cookie_value_raw': (
                '66636334353064312d383637342d316264332d343037342d6132343063666'
                '6356335623100'),
            'data_type': 'msie:webcache:cookie',
            'entry_identifier': 13,
            'flags': 0x80082401,
            'request_domain': 'com.associates-amazon' }

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 69)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

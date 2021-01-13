#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows IIS log parser."""

import unittest

from plaso.parsers import iis

from tests.parsers import test_lib


class WinIISUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows IIS parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 12)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'dest_ip': '10.10.10.100',
        'dest_port': 80,
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/some/image/path/something.jpg',
        'source_ip': '10.10.10.100',
        'timestamp': '2013-07-30 00:00:00.000000',
        'user_agent': (
            'Mozilla/4.0+(compatible;+Win32;+WinHttp.WinHttpRequest.5)')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'iis:log:line',
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/some/image/path/something.jpg',
        'timestamp': '2013-07-30 00:00:05.000000'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'iis:log:line',
        'dest_ip': '10.10.10.100',
        'dest_port': 80,
        'http_method': 'GET',
        'http_status': 404,
        'requested_uri_stem': '/some/image/path/something.htm',
        'source_ip': '22.22.22.200',
        'timestamp': '2013-07-30 00:00:03.000000',
        'user_agent': (
            'Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_6_8)+AppleWebKit/'
            '534.57.2+(KHTML,+like+Gecko)+Version/5.1.7+Safari/534.57.2')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'cs_uri_query': 'ID=ERROR[`cat%20passwd|echo`]',
        'data_type': 'iis:log:line'}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

  def testParseWithoutDate(self):
    """Tests the Parse function with logs without a date column."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis_without_date.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 11)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'protocol_version': 'HTTP/1.1',
        'timestamp': '2013-07-30 00:00:03.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()

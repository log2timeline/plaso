#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows IIS log parser."""

import unittest

from plaso.parsers import iis

from tests.parsers import test_lib


class WinIISUnitTest(test_lib.ParserTestCase):
  """Tests for the Windows IIS parser."""

  def testParse(self):
    """Tests the Parse function with an IIS 6 log file."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis6.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30 00:00:00',
        'dest_ip': '10.10.10.100',
        'dest_port': 80,
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/some/image/path/something.jpg',
        'source_ip': '10.10.10.100',
        'user_agent': (
            'Mozilla/4.0+(compatible;+Win32;+WinHttp.WinHttpRequest.5)')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30 00:00:05',
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/some/image/path/something.jpg'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30 00:00:03',
        'dest_ip': '10.10.10.100',
        'dest_port': 80,
        'http_method': 'GET',
        'http_status': 404,
        'requested_uri_stem': '/some/image/path/something.htm',
        'source_ip': '22.22.22.200',
        'user_agent': (
            'Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_6_8)+AppleWebKit/'
            '534.57.2+(KHTML,+like+Gecko)+Version/5.1.7+Safari/534.57.2')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'cs_uri_query': 'ID=ERROR[`cat%20passwd|echo`]',
        'data_type': 'iis:log:line'}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

  def testParseWithIIS7SQLIFile(self):
    """Tests the Parse function with an IIS 7 log file with SQLI."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis7_sqli.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2015-10-16 13:01:02',
        'dest_ip': '111.111.111.111',
        'dest_port': 443,
        'http_method': 'GET',
        'http_status': 500,
        'requested_uri_stem': '/foo/bar/baz.asp',
        'source_ip': '222.222.222.222',
        'user_agent': (
            'Mozilla/5.0+(Macintosh;+Intel+Mac+OS+X+10_9_2)+AppleWebKit/'
            '537.36+(KHTML,+like+Gecko)+Chrome/34.0.1847.131+Safari/537.36')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseWithIIS7OWAFile(self):
    """Tests the Parse function with an IIS 7 OWA log file."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis7_owa.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2015-12-31 00:19:48',
        'dest_ip': '10.11.2.3',
        'dest_port': 443,
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/owa/',
        'source_ip': '77.123.22.98',
        'user_agent': (
            'Mozilla/5.0+(Windows+NT+6.1;+WOW64)+AppleWebKit/537.36+'
            '(KHTML,+like+Gecko)+Chrome/39.0.2171.95+Safari/537.36')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseWithoutDate(self):
    """Tests the Parse function with logs without a date column."""
    parser = iis.WinIISParser()
    storage_writer = self._ParseFile(['iis_without_date.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30 00:00:03',
        'protocol_version': 'HTTP/1.1',
        'timestamp': '2013-07-30 00:00:03.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()

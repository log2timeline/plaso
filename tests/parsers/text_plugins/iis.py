#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows IIS log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import iis

from tests.parsers.text_plugins import test_lib


class WinIISTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Windows IIS text parser plugin."""

  def testProcessWithIIS6Log(self):
    """Tests the Process function with an IIS 6 log file."""
    plugin = iis.WinIISTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['iis6.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 12)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30T00:00:00+00:00',
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
        'date_time': '2013-07-30T00:00:05+00:00',
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/some/image/path/something.jpg'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30T00:00:03+00:00',
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

  def testProcessWithIIS7LogAndSQLI(self):
    """Tests the Process function with an IIS 7 log file with SQLI."""
    plugin = iis.WinIISTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['iis7_sqli.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2015-10-16T13:01:02+00:00',
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

  def testProcessWithIIS7OWALog(self):
    """Tests the Process function with an IIS 7 OWA log file."""
    plugin = iis.WinIISTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['iis7_owa.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2015-12-31T00:19:48+00:00',
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

  def testProcessWithoutDate(self):
    """Tests the Process function with logs without a date column."""
    plugin = iis.WinIISTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['iis_without_date.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 11)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2013-07-30T00:00:03+00:00',
        'protocol_version': 'HTTP/1.1',
        'timestamp': '2013-07-30 00:00:03.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testProcessWithIIS10Log(self):
    """Tests the Process function with an IIS 10 log file."""
    plugin = iis.WinIISTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['iis10.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'iis:log:line',
        'date_time': '2021-04-01T00:00:21+00:00',
        'dest_ip': '111.111.111.111',
        'dest_port': 80,
        'http_method': 'GET',
        'http_status': 200,
        'requested_uri_stem': '/foo/bar/baz.asp',
        'source_ip': '222.222.222.222',
        'user_agent': (
            'Mozilla/5.0+(Windows+NT+5.1)+AppleWebKit/'
            '537.36+(KHTML,+like+Gecko)'
            '+Chrome/35.0.2309.372+Safari/537.36')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()

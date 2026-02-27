#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Squid access log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import squid_access

from tests.parsers.text_plugins import test_lib


class SquidAccessLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for Squid access log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = squid_access.SquidAccessLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['squid_access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test first event - TCP_TUNNEL with minimal fields
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 39,
        'client_ip': '1.2.3.4',
        'content_type': None,
        'hierarchy_info': 'HIER_DIRECT/1.2.3.4',
        'http_request': 'CONNECT domain.xyz:443',
        'http_status': 200,
        'recorded_time': '2023-03-04T23:15:34.079000+00:00',
        'response_time': 1234,
        'result_code': 'TCP_TUNNEL',
        'user_id': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test TCP_MISS with user and content type
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 5432,
        'client_ip': '192.168.1.100',
        'content_type': 'text/html',
        'hierarchy_info': 'HIER_DIRECT/93.184.216.34',
        'http_request': 'GET http://example.com/index.html',
        'http_status': 200,
        'recorded_time': '2023-03-04T23:15:35.123000+00:00',
        'response_time': 567,
        'result_code': 'TCP_MISS',
        'user_id': 'user1'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

    # Test TCP_HIT event
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 0,
        'client_ip': '10.0.0.50',
        'content_type': 'image/png',
        'hierarchy_info': 'NONE/-',
        'http_request': 'GET http://example.com/logo.png',
        'http_status': 304,
        'recorded_time': '2023-03-04T23:15:36.456000+00:00',
        'response_time': 890,
        'result_code': 'TCP_HIT',
        'user_id': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    # Test IPv6 address
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 1024,
        'client_ip': '2001:db8::1',
        'content_type': 'text/html',
        'hierarchy_info': 'HIER_DIRECT/93.184.216.34',
        'http_request': 'GET http://example.com/missing.html',
        'http_status': 404,
        'recorded_time': '2023-03-04T23:15:37.789000+00:00',
        'response_time': 123,
        'result_code': 'TCP_MISS',
        'user_id': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

    # Test POST request
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 256,
        'client_ip': '172.16.0.1',
        'content_type': 'application/json',
        'hierarchy_info': 'HIER_NONE/-',
        'http_request': 'POST http://example.com/api/data',
        'http_status': 403,
        'recorded_time': '2023-03-04T23:15:38.012000+00:00',
        'response_time': 456,
        'result_code': 'TCP_DENIED',
        'user_id': None}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 5)
    self.CheckEventData(event_data, expected_event_values)

    # Test user with domain format
    expected_event_values = {
        'data_type': 'squid:access_log:entry',
        'bytes_transferred': 54321,
        'client_ip': '10.10.10.10',
        'content_type': None,
        'hierarchy_info': 'HIER_DIRECT/10.20.30.40',
        'http_request': 'CONNECT secure.example.com:443',
        'http_status': 200,
        'recorded_time': '2023-03-04T23:15:40.678000+00:00',
        'response_time': 234,
        'result_code': 'TCP_TUNNEL',
        'user_id': 'user@domain.com'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 7)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

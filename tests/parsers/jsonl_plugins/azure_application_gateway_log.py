# -*- coding: utf-8 -*
"""Tests for the Azure Application Gateway Access log files parser."""

import unittest

from plaso.parsers.jsonl_plugins import azure_application_gateway_log

from tests.parsers.jsonl_plugins import test_lib


class AzureApplicationGatewayAccessLogJSONLPluginTest(
    test_lib.JSONLPluginTestCase):
  """Tests for the Azure Application Gateway Access log files parser."""

  def testProcess(self):
    """Tests the Process function."""
    plugin_module = azure_application_gateway_log
    plugin = plugin_module.AzureApplicationGatewayAccessLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(
        ['azure_application_gateway_access.json'], plugin)

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
        'client_ip': '185.42.129.24',
        'client_port': 45057,
        'client_response_time': 0,
        'date_time': '2021-10-14 22:17:11.000000',
        'host': '20.110.30.194',
        'http_method': 'GET',
        'http_status': 200,
        'http_version': 'HTTP/1.1',
        'instance_identifier': 'appgw_2',
        'original_host': '20.110.30.194',
        'original_request_uri': '/',
        'received_bytes': 184,
        'request_uri': '/',
        'sent_bytes': 466,
        'server_response_latency': '0.028',
        'server_routed': '52.239.221.65:443',
        'server_status': '200',
        'ssl_cipher': 'ECDHE-RSA-AES256-GCM-SHA384',
        'ssl_client_verify': 'NONE',
        'ssl_enabled': 'on',
        'ssl_protocol': 'TLSv1.2',
        'time_taken': 0.034,
        'transaction_identifier': '592d1649f75a8d480a3c4dc6a975309d',
        'user_agent': (
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'),
        'waf_evaluation_time': '0.000',
        'waf_mode': 'Detection'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'client_ip': '185.42.129.24',
        'client_port': 45057,
        'client_response_time': 0,
        'date_time': '2021-10-14 22:17:12.000000',
        'host': '20.110.30.194',
        'http_method': 'GET',
        'http_status': 400,
        'http_version': 'HTTP/1.1',
        'instance_identifier': 'appgw_2',
        'original_host': '20.110.30.194',
        'original_request_uri': '/',
        'received_bytes': 184,
        'request_uri': '/',
        'sent_bytes': 466,
        'server_response_latency': '0.028',
        'server_routed': '52.239.221.65:443',
        'server_status': '200',
        'ssl_cipher': 'ECDHE-RSA-AES256-GCM-SHA384',
        'ssl_client_verify': 'NONE',
        'ssl_enabled': 'on',
        'ssl_protocol': 'TLSv1.2',
        'time_taken': 0.034,
        'transaction_identifier': '592d1649f75a8d480a3c4dc6a975309d',
        'user_agent': (
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'),
        'waf_evaluation_time': '0.000',
        'waf_mode': 'Detection'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()

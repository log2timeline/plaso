# -*- coding: utf-8 -*
"""Tests for the Azure Application Gateway Access logging parser."""

import unittest

from plaso.parsers import azure_application_gateway_access
from tests.parsers import test_lib


class AzureApplicationGatewayAccessLogTest(test_lib.ParserTestCase):
  """Tests for the Azure Application Gateway Access logging parser."""

  def testParseAzureActivityLog(self):
    """Tests that Azure Application Gateway Access logs are correctly parsed."""

    expected_timestamps = [
      '2021-10-14 22:17:11.000000',
      '2021-10-14 22:17:12.000000',
    ]

    # pylint: disable=line-too-long
    expected_events = [
      {
        "instance_id": "appgw_2",
        "client_ip": "185.42.129.24",
        "client_port": 45057,
        "http_method": "GET",
        "original_request_uri_with_args": "/",
        "request_uri": "/",
        "request_query": "",
        "user_agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
        "http_status": 200,
        "http_version": "HTTP/1.1",
        "received_bytes": 184,
        "sent_bytes": 466,
        "client_response_time": 0,
        "time_taken": 0.034,
        "waf_evaluation_time": "0.000",
        "waf_mode": "Detection",
        "transaction_id": "592d1649f75a8d480a3c4dc6a975309d",
        "ssl_enabled": "on",
        "ssl_cipher": "ECDHE-RSA-AES256-GCM-SHA384",
        "ssl_protocol": "TLSv1.2",
        "ssl_client_verify": "NONE",
        "ssl_client_certificate_fingerprint": "",
        "ssl_client_certificate_issuer_name": "",
        "server_routed": "52.239.221.65:443",
        "server_status": "200",
        "server_response_latency": "0.028",
        "original_host": "20.110.30.194",
        "host": "20.110.30.194",
      },
      {
        "instance_id": "appgw_2",
        "client_ip": "185.42.129.24",
        "client_port": 45057,
        "http_method": "GET",
        "original_request_uri_with_args": "/",
        "request_uri": "/",
        "request_query": "",
        "user_agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
        "http_status": 400,
        "http_version": "HTTP/1.1",
        "received_bytes": 184,
        "sent_bytes": 466,
        "client_response_time": 0,
        "time_taken": 0.034,
        "waf_evaluation_time": "0.000",
        "waf_mode": "Detection",
        "transaction_id": "592d1649f75a8d480a3c4dc6a975309d",
        "ssl_enabled": "on",
        "ssl_cipher": "ECDHE-RSA-AES256-GCM-SHA384",
        "ssl_protocol": "TLSv1.2",
        "ssl_client_verify": "NONE",
        "ssl_client_certificate_fingerprint": "",
        "ssl_client_certificate_issuer_name": "",
        "server_routed": "52.239.221.65:443",
        "server_status": "200",
        "server_response_latency": "0.028",
        "original_host": "20.110.30.194",
        "host": "20.110.30.194",
      },
    ]
    # pylint: enable=line-too-long

    parser = azure_application_gateway_access.AzureApplicationGatewayAccessParser() # pylint: disable=line-too-long
    storage_writer = self._ParseFile(
      ['azure_application_gateway_access.json'], parser
    )

    self.assertEqual(storage_writer.number_of_events, 2)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = storage_writer.GetEvents()
    for event, expected_event, expected_timestamp in zip(
      events, expected_events, expected_timestamps
    ):
      self.CheckTimestamp(event.timestamp, expected_timestamp)
      self.CheckEventValues(storage_writer, event, expected_event)


if __name__ == '__main__':
  unittest.main()

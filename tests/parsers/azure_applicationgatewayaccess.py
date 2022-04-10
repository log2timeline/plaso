# -*- coding: utf-8 -*
"""Tests for the Azure Application Gateway Access logging parser."""

import unittest

from plaso.parsers import azure_applicationgatewayaccess
from tests.parsers import test_lib


class AzureApplicationGatewayAccessLogTest(test_lib.ParserTestCase):
  """Tests for the Azure Application Gateway Access logging parser."""

  def testParseAzureActivityLog(self):
    """Tests that Azure Application Gateway Access logs are correctly parsed."""

    expected_timestamps = [
      '2021-10-14 22:17:11.000000',
      '2021-10-14 22:17:12.000000'
    ]

    # pylint: disable=line-too-long
    expected_events = [
        {
          "instanceId": "appgw_2",
          "clientIP": "185.42.129.24",
          "clientPort": 45057,
          "httpMethod": "GET",
          "originalRequestUriWithArgs": "/",
          "requestUri": "/",
          "requestQuery": "",
          "userAgent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
          "httpStatus": 200,
          "httpVersion": "HTTP/1.1",
          "receivedBytes": 184,
          "sentBytes": 466,
          "clientResponseTime": 0,
          "timeTaken": 0.034,
          "WAFEvaluationTime": "0.000",
          "WAFMode": "Detection",
          "transactionId": "592d1649f75a8d480a3c4dc6a975309d",
          "sslEnabled": "on",
          "sslCipher": "ECDHE-RSA-AES256-GCM-SHA384",
          "sslProtocol": "TLSv1.2",
          "sslClientVerify": "NONE",
          "sslClientCertificateFingerprint": "",
          "sslClientCertificateIssuerName": "",
          "serverRouted": "52.239.221.65:443",
          "serverStatus": "200",
          "serverResponseLatency": "0.028",
          "originalHost": "20.110.30.194",
          "host": "20.110.30.194"
      },
      {
        "instanceId": "appgw_2",
        "clientIP": "185.42.129.24",
        "clientPort": 45057,
        "httpMethod": "GET",
        "originalRequestUriWithArgs": "/",
        "requestUri": "/",
        "requestQuery": "",
        "userAgent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
        "httpStatus": 400,
        "httpVersion": "HTTP/1.1",
        "receivedBytes": 184,
        "sentBytes": 466,
        "clientResponseTime": 0,
        "timeTaken": 0.034,
        "WAFEvaluationTime": "0.000",
        "WAFMode": "Detection",
        "transactionId": "592d1649f75a8d480a3c4dc6a975309d",
        "sslEnabled": "on",
        "sslCipher": "ECDHE-RSA-AES256-GCM-SHA384",
        "sslProtocol": "TLSv1.2",
        "sslClientVerify": "NONE",
        "sslClientCertificateFingerprint": "",
        "sslClientCertificateIssuerName": "",
        "serverRouted": "52.239.221.65:443",
        "serverStatus": "200",
        "serverResponseLatency": "0.028",
        "originalHost": "20.110.30.194",
        "host": "20.110.30.194"
      }
    ]
    # pylint: enable=line-too-long

    parser = azure_applicationgatewayaccess.AzureApplicationGatewayAccessParser()
    storage_writer = self._ParseFile(['azure_application_gateway_access.json'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = storage_writer.GetEvents()
    for event, expected_event, expected_timestamp in zip(
        events, expected_events, expected_timestamps):
      self.CheckTimestamp(event.timestamp, expected_timestamp)
      self.CheckEventValues(storage_writer, event, expected_event)


if __name__ == '__main__':
  unittest.main()

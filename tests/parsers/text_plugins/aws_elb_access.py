#!/usr/bin/env python3
"""Tests for the AWS ELB access log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import aws_elb_access

from tests.parsers.text_plugins import test_lib


class AWSELBTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the AWS ELB access log text parser plugin."""

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = aws_elb_access.AWSELBTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'https 2020-01-11T16:55:20.356586Z '
        b'app/production-web/jf29fj2198ejf922 192.168.1.10:44325 '
        b'192.168.1.123:32869 0.013 0.164 0.000 200 200 391 107999 '
        b'"GET https://www.domain.name:443/ HTTP/1.1" "Mozilla/5.0 '
        b'(compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)" '
        b'ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 '
        b'arn:aws:elasticloadbalancing:us-east-2:123456789123 "XXXXXXX" '
        b'"www.domain.name" "arn:aws:abc:us-east-2:234567891234:certificate" '
        b'2 2020-01-11T16:55:19.624000Z "waf,forward" "-" "-" '
        b'"192.168.1.123:32869" "200" "-" "-"\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcess(self):
    """Tests the Process function."""
    plugin = aws_elb_access.AWSELBTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['aws_elb_access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 16)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'actions_executed': 'waf,forward',
        'chosen_cert_arn': 'arn:aws:abc:us-east-2:234567891234:certificate',
        'classification': None,
        'classification_reason': None,
        'data_type': 'aws:elb:access',
        'destination_group_arn': (
            'arn:aws:elasticloadbalancing:us-east-2:123456789123'),
        'destination_ip_address': '192.168.1.123',
        'destination_list': ['192.168.1.123:32869'],
        'destination_port': 32869,
        'destination_processing_duration': '0.164',
        'destination_status_code': 200,
        'destination_status_code_list': '200',
        'domain_name': 'www.domain.name',
        'elb_status_code': 200,
        'error_reason': None,
        'matched_rule_priority': 2,
        'received_bytes': 391,
        'redirect_url': None,
        'request': 'GET https://www.domain.name:443/ HTTP/1.1',
        'request_processing_duration': '0.013',
        'request_type': 'https',
        'resource_identifier': 'app/production-web/jf29fj2198ejf922',
        'response_processing_duration': '0.000',
        'sent_bytes': 107999,
        'source_ip_address': '192.168.1.10',
        'source_port': 44325,
        'ssl_cipher': 'ECDHE-RSA-AES128-GCM-SHA256',
        'ssl_protocol': 'TLSv1.2',
        'request_time': '2020-01-11T16:55:19.624000+00:00',
        'response_time': '2020-01-11T16:55:20.356586+00:00',
        'trace_identifier': 'XXXXXXX',
        'user_agent': (
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; '
            'Trident/6.0)')}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the AWS ELB access log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import aws_elb_access

from tests.parsers.text_plugins import test_lib


class AWSELBTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the AWS ELB access log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = aws_elb_access.AWSELBTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['aws_elb_access.log'], plugin)

    # Test number of events and warnings
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 20)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which the text parser plugin generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'actions_executed': 'waf,forward',
        'chosen_cert_arn': 'arn:aws:abc:us-east-2:234567891234:certificate',
        'classification': '-',
        'classification_reason': '-',
        'data_type': 'aws:elb:access',
        'destination_group_arn': (
            'arn:aws:elasticloadbalancing:us-east-2:123456789123'),
        'destination_ip_address': '192.168.1.123',
        'destination_list': ['192.168.1.123:32869'],
        'destination_port': 32869,
        'destination_processing_time': '0.164',
        'destination_status_code': 200,
        'destination_status_code_list': '200',
        'domain_name': 'www.domain.name',
        'elb_status_code': 200,
        'error_reason': '-',
        'matched_rule_priority': 2,
        'received_bytes': 391,
        'redirect_url': '-',
        'request': 'GET https://www.domain.name:443/ HTTP/1.1',
        'request_processing_time': '0.013',
        'request_type': 'https',
        'resource_identifier': 'app/production-web/jf29fj2198ejf922',
        'response_processing_time': '0.000',
        'sent_bytes': 107999,
        'source_ip_address': '192.168.1.10',
        'source_port': 44325,
        'ssl_cipher': 'ECDHE-RSA-AES128-GCM-SHA256',
        'ssl_protocol': 'TLSv1.2',
        'timestamp': '2020-01-11 16:55:19.000000',
        'trace_identifier': '"XXXXXXX"',
        'user_agent': (
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; '
            'Trident/6.0)')}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'actions_executed': 'waf,forward',
        'chosen_cert_arn': 'arn:aws:abc:us-east-2:234567891234:certificate',
        'classification': '-',
        'classification_reason': '-',
        'data_type': 'aws:elb:access',
        'destination_group_arn': (
            'arn:aws:elasticloadbalancing:us-east-2:123456789123'),
        'destination_ip_address': '192.168.1.123',
        'destination_list': ['192.168.1.123:32869'],
        'destination_port': 32869,
        'destination_processing_time': '0.164',
        'destination_status_code': 200,
        'destination_status_code_list': '200',
        'domain_name': 'www.domain.name',
        'elb_status_code': 200,
        'error_reason': '-',
        'matched_rule_priority': 2,
        'received_bytes': 391,
        'redirect_url': '-',
        'request': 'GET https://www.domain.name:443/ HTTP/1.1',
        'request_processing_time': '0.013',
        'request_type': 'https',
        'resource_identifier': 'app/production-web/jf29fj2198ejf922',
        'response_processing_time': '0.000',
        'sent_bytes': 107999,
        'source_ip_address': '192.168.1.10',
        'source_port': 44325,
        'ssl_cipher': 'ECDHE-RSA-AES128-GCM-SHA256',
        'ssl_protocol': 'TLSv1.2',
        'timestamp': '2020-01-11 16:55:20.000000',
        'trace_identifier': '"XXXXXXX"',
        'user_agent': (
            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; '
            'Trident/6.0)')}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # TODO: add test for request_creation_time event
    # '2020-01-11T16:55:19.624000Z'


if __name__ == '__main__':
  unittest.main()

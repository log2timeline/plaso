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
    self.assertEqual(number_of_events, 26)

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

    expected_event_values = {
        'timestamp': '2021-05-13 23:39:43.000000',
        'resource_identifier': 'my-loadbalancer',
        'source_ip_address': '192.168.131.39',
        'source_port': 2817,
        'destination_ip_address': '10.0.0.1',
        'destination_port': 80,
        'request_processing_time': '0.000073',
        'destination_processing_time': '0.001048',
        'response_processing_time': '0.000057',
        'elb_status_code': 200,
        'destination_status_code': 200,
        'received_bytes': 0,
        'sent_bytes': 29,
        'request': 'GET http://www.example.com:80/ HTTP/1.1',
        'user_agent': 'curl/7.38.0',
        'ssl_cipher': '-',
        'ssl_protocol': '-'
    }
    self.CheckEventValues(storage_writer, events[20], expected_event_values)

    expected_event_values = {
        'timestamp': '2021-05-13 23:39:46.000000',
        'resource_identifier': 'my-loadbalancer',
        'source_ip_address': '192.168.131.39',
        'source_port': 2817,
        'destination_ip_address': '10.0.0.1',
        'destination_port': 80,
        'request_processing_time': '0.001065',
        'destination_processing_time': '0.000015',
        'response_processing_time': '0.000023',
        'elb_status_code': '-',
        'destination_status_code': '-',
        'received_bytes': '-1',
        'sent_bytes': '-1',
        'request': '- - - ',
        'user_agent': '-',
        'ssl_cipher': 'ECDHE-ECDSA-AES128-GCM-SHA256',
        'ssl_protocol': 'TLSv1.2'
    }
    self.CheckEventValues(storage_writer, events[23], expected_event_values)

    expected_event_values = {
        'version':'tls',
        'version':'2.0',
        'timestamp': '2022-04-01 08:51:42.000000',
        'resource_identifier': 'net/my-network-loadbalancer/c6e77e28c25b2234',
        'listener': 'g3d4b5e8bb8464cd',
        'source_ip_address': '72.21.218.154',
        'source_port': 51341,
        'destination_ip_address': '172.100.100.185',
        'destination_port': 443,
        'connection_time': 5,
        'handshake_time': 2,
        'received_bytes': 98,
        'sent_bytes': 246,
        'incoming_tls_alert': '-',
        'chosen_cert_arn': (
            'arn:aws:acm:us-east-2:671290407336:certificate/2a108f19-aded-46b0-8493-c63eb1ef4a99'),
        'chosen_cert_serial': '-',
        'tls_cipher': 'ECDHE-RSA-AES128-SHA',
        'tls_protocol_version': 'tlsv12',
        'tls_named_group': '-',
        'domain_name': (
            'my-network-loadbalancer-c6e77e28c25b2234.elb.us-east-2.amazonaws.com'),
        'alpn_fe_protocol': 'h2',
        'alpn_be_protocol': 'h2',
        'alpn_client_preference_list': 'h2'
    }
    self.CheckEventValues(storage_writer, events[24], expected_event_values)

    # TODO: add test for request_creation_time event
    # '2020-01-11T16:55:19.624000Z'


if __name__ == '__main__':
  unittest.main()

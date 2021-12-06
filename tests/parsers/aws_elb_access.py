#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Apache access log parser."""

import unittest

from plaso.parsers import aws_elb_access
from tests.parsers import test_lib


class AWSELBUnitTest(test_lib.ParserTestCase):
  """Tests for an AWS ELB access log parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = aws_elb_access.AWSELBParser()
    storage_writer = self._ParseFile(['aws_elb_access.log'], parser)

    # Test number of events and warnings
    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which parser generates events is nondeterministic hence
    # we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_timestamps = ['2020-01-11 16:55:20.000000']

    # pylint: disable=line-too-long
    expected_event_values = {
        "actions_executed": "waf,forward",
        "chosen_cert_arn": "arn:aws:abc:us-east-2:234567891234:certificate",
        "classification": "-",
        "classification_reason": "-",
        "client_ip_address": "192.168.1.10",
        "client_port": 44325,
        "data_type": "aws:elb:access",
        "domain_name": "www.domain.name",
        "resource_identifier": "app/production-web/jf29fj2198ejf922",
        "elb_status_code": 200,
        "error_reason": "-",
        "matched_rule_priority": 2,
        "received_bytes": 391,
        "redirect_url": "-",
        "request": "GET https://www.domain.name:443/ HTTP/1.1",
        "request_creation_time": "2020-01-11T16:55:19.624000Z",
        "request_processing_time": "0.013",
        "response_processing_time": "0.000",
        "sent_bytes": 107999,
        "ssl_cipher": "ECDHE-RSA-AES128-GCM-SHA256",
        "ssl_protocol": "TLSv1.2",
        "target_group_arn": "arn:aws:elasticloadbalancing:us-east-2:123456789123",
        "target_ip_address": "192.168.1.123",
        "target_port": 32869,
        "target_port_list": "192.168.1.123:32869",
        "target_processing_time": "0.164",
        "target_status_code": 200,
        "target_status_code_list": "200",
        "trace_identifier": "\"XXXXXXX\"",
        "type": "https",
        "user_agent":
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)"}

    # Test for the expected timestamp value
    self.CheckTimestamp(events[0].timestamp, expected_timestamps[0])

    # Test the rest of the expected values
    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
